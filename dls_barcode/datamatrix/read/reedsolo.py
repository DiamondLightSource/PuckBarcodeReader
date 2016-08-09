"""
Reed Solomon
============
Reed-Solomon Error code correction library
Based on original from: https://pypi.python.org/pypi/reedsolo
Significant modifications for use with Datamatrix by Kris Ward (kris.ward@diamond.ac.uk)

The following is the header from the original author:
------------------------------------------------------------------------------------------------------
| A pure-python `Reed Solomon <http://en.wikipedia.org/wiki/Reed%E2%80%93Solomon_error_correction>`_
| encoder/decoder, based on the wonderful tutorial at
| `wikiversity <http://en.wikiversity.org/wiki/Reed%E2%80%93Solomon_codes_for_coders>`_,
| written by "Bobmath".
|
| I only consolidated the code a little and added exceptions and a simple API.
| To my understanding, the algorithm can correct up to ``nsym/2`` of the errors in
| the message, where ``nsym`` is the number of bytes in the error correction code (ECC).
| The code should work on pretty much any reasonable version of python (2.4-3.2),
| but I'm only testing on 2.5-3.2.
|
| .. note::
|    I claim no authorship of the code, and take no responsibility for the correctness
|    of the algorithm. It's way too much finite-field algebra for me :)
|
|  I've released this package as I needed an ECC codec for another project I'm working on,
|  and I couldn't find anything on the web (that still works).
|
|    The algorithm itself can handle messages up to 255 bytes, including the ECC bytes. The
|    ``RSCodec`` class will split longer messages into chunks and encode/decode them separately;
|    it shouldn't make a difference from an API perspective.
--------------------------------------------------------------------------------------------------------

"""

# Values specific to encoding used for datamatrix.
DATAMATRIX_PRIMITIVE = 0x12d
DATAMATRIX_GEN_BASE = 1


class ReedSolomonError(Exception):
    def __init__(self, message):
        self.message = message


class ReedSolomonDecoder:
    def __init__(self):
        self.gf = GaloisField()

    def decode(self, encoded_msg, num_data_bytes):
        return self._correct_msg(encoded_msg, num_data_bytes)

    def _correct_msg(self, msg_in, num_symbols):
        if len(msg_in) > 255:
            raise ValueError("message too long")

        msg_out = list(msg_in)  # copy of message

        # find erasures
        erase_pos = []
        for i in range(0, len(msg_out)):
            if msg_out[i] < 0:
                msg_out[i] = 0
                erase_pos.append(i)

        if len(erase_pos) > num_symbols:
            raise ReedSolomonError("Too many erasures to correct")

        syndromes = self._calculate_syndromes(msg_out, num_symbols)
        if max(syndromes) == 0:
            return msg_out[:-num_symbols]  # no errors

        forney_syndromes = self._forney_syndromes(syndromes, erase_pos, len(msg_out))
        err_pos = self._find_errors(forney_syndromes, len(msg_out))
        if err_pos is None:
            raise ReedSolomonError("Could not locate error")

        self._correct_errata(msg_out, syndromes, erase_pos + err_pos)
        syndromes = self._calculate_syndromes(msg_out, num_symbols)

        if max(syndromes) > 0:
            raise ReedSolomonError("Could not correct message")

        return msg_out[:-num_symbols]

    def _calculate_syndromes(self, msg, num_symbols):
        return [self.gf.poly_eval(msg, self.gf.exp(i + DATAMATRIX_GEN_BASE)) for i in range(num_symbols)]

    def _forney_syndromes(self, syndromes, erase_positions, nmess):
        fsynd = list(syndromes)  # make a copy
        for i in range(0, len(erase_positions)):
            x = self.gf.exp(nmess - 1 - erase_positions[i])
            for i in range(0, len(fsynd) - 1):
                fsynd[i] = self.gf.mul(fsynd[i], x) ^ fsynd[i + 1]
            fsynd.pop()
        return fsynd

    def _find_errors(self, syndromes, nmess):
        # find error locator polynomial with Berlekamp-Massey algorithm
        err_poly = [1]
        old_poly = [1]
        for i in range(0, len(syndromes)):
            old_poly.append(0)
            delta = syndromes[i]
            for j in range(1, len(err_poly)):
                delta ^= self.gf.mul(err_poly[len(err_poly) - 1 - j], syndromes[i - j])
            if delta != 0:
                if len(old_poly) > len(err_poly):
                    new_poly = self.gf.poly_scale(old_poly, delta)
                    old_poly = self.gf.poly_scale(err_poly, self.gf.div(1, delta))
                    err_poly = new_poly
                err_poly = self.gf.poly_add(err_poly, self.gf.poly_scale(old_poly, delta))

        errs = len(err_poly) - 1
        if errs * 2 > len(syndromes):
            raise ReedSolomonError("Too many errors to correct")

        # find zeros of error polynomial
        err_pos = []
        for i in range(0, nmess):
            if self.gf.poly_eval(err_poly, self.gf.exp(255 - i)) == 0:
                err_pos.append(nmess - 1 - i)
        if len(err_pos) != errs:
            return None  # couldn't find error locations
        return err_pos

    def _correct_errata(self, msg, syndromes, pos):
        # calculate error locator polynomial
        q = [1]
        for i in range(0, len(pos)):
            x = self.gf.exp(len(msg) - 1 - pos[i])
            q = self.gf.poly_mul(q, [x, 1])
        # calculate error evaluator polynomial
        p = syndromes[0:len(pos)]
        p.reverse()
        p = self.gf.poly_mul(p, q)
        p = p[len(p) - len(pos):len(p)]
        # formal derivative of error locator eliminates even terms
        q = q[len(q) & 1:len(q):2]
        # compute corrections
        for i in range(0, len(pos)):
            x = self.gf.exp(pos[i] + 256 - len(msg))
            y = self.gf.poly_eval(p, x)
            z = self.gf.poly_eval(q, self.gf.mul(x, x))

            adj = self.gf.div(y, self.gf.mul(x, z))
            if DATAMATRIX_GEN_BASE != 0:
                adj = self.gf.mul(adj, x)
            msg[pos[i]] ^= adj

    def encode(self, msg_in, num_ecc_symbols):
        if len(msg_in) + num_ecc_symbols > 255:
            raise ValueError("message too long")

        gen = self._generator_poly(num_ecc_symbols)
        msg_out = bytearray(len(msg_in) + num_ecc_symbols)
        msg_out[:len(msg_in)] = msg_in
        for i in range(0, len(msg_in)):
            coef = msg_out[i]
            if coef != 0:
                for j in range(0, len(gen)):
                    msg_out[i + j] ^= self.gf.mul(gen[j], coef)
        msg_out[:len(msg_in)] = msg_in
        return msg_out

    def _generator_poly(self, num_symbols):
        g = [1]
        for i in range(0, num_symbols):
            g = self.gf.poly_mul(g, [1, self.gf.exp(i + DATAMATRIX_GEN_BASE)])
        return g


class GaloisField:
    def __init__(self):
        # Generate the exponential and logarithm tables
        self._exp = [1] * 512
        self._log = [0] * 256

        x = 1
        for i in range(1, 255):
            x <<= 1
            if x & 0x100:
                x ^= DATAMATRIX_PRIMITIVE

            self._exp[i] = x
            self._log[x] = i

        for i in range(255, 512):
            self._exp[i] = self._exp[i - 255]

    def exp(self, i):
        return self._exp[i]

    def mul(self, x, y):
        if x == 0 or y == 0:
            return 0
        return self._exp[self._log[x] + self._log[y]]

    def div(self, x, y):
        if y == 0:
            raise ZeroDivisionError()
        if x == 0:
            return 0
        return self._exp[self._log[x] + 255 - self._log[y]]

    def poly_scale(self, p, x):
        return [self.mul(p[i], x) for i in range(0, len(p))]

    def poly_add(self, p, q):
        r = [0] * max(len(p), len(q))
        for i in range(0, len(p)):
            r[i + len(r) - len(p)] = p[i]
        for i in range(0, len(q)):
            r[i + len(r) - len(q)] ^= q[i]
        return r

    def poly_mul(self, p, q):
        r = [0] * (len(p) + len(q) - 1)
        for j in range(0, len(q)):
            for i in range(0, len(p)):
                r[i + j] ^= self.mul(p[i], q[j])
        return r

    def poly_eval(self, p, x):
        y = p[0]
        for i in range(1, len(p)):
            y = self.mul(y, x) ^ p[i]
        return y
