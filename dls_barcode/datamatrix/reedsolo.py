"""
Reed Solomon
============
Reed-Solomon Error code correction library
Original from: https://pypi.python.org/pypi/reedsolo
Modifications for use with Datamatrix by Kris Ward (kris.ward@diamond.ac.uk)

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
    pass

def RSDecode(encoded_msg, num_data_bytes):
    return rs_correct_msg(encoded_msg, num_data_bytes)

# Generate the exponential and logarithm tables
gf_exp = [1] * 512
gf_log = [0] * 256
x = 1
for i in range(1, 255):
    x <<= 1
    if x & 0x100:
        x ^= DATAMATRIX_PRIMITIVE
    gf_exp[i] = x
    gf_log[x] = i
for i in range(255, 512):
    gf_exp[i] = gf_exp[i - 255]



def gf_mul(x, y):
    if x == 0 or y == 0:
        return 0
    return gf_exp[gf_log[x] + gf_log[y]]

def gf_div(x, y):
    if y == 0:
        raise ZeroDivisionError()
    if x == 0:
        return 0
    return gf_exp[gf_log[x] + 255 - gf_log[y]]

def gf_poly_scale(p, x):
    return [gf_mul(p[i], x) for i in range(0, len(p))]

def gf_poly_add(p, q):
    r = [0] * max(len(p), len(q))
    for i in range(0, len(p)):
        r[i + len(r) - len(p)] = p[i]
    for i in range(0, len(q)):
        r[i + len(r) - len(q)] ^= q[i]
    return r

def gf_poly_mul(p, q):
    r = [0] * (len(p) + len(q) - 1)
    for j in range(0, len(q)):
        for i in range(0, len(p)):
            r[i + j] ^= gf_mul(p[i], q[j])
    return r

def gf_poly_eval(p, x):
    y = p[0]
    for i in range(1, len(p)):
        y = gf_mul(y, x) ^ p[i]
    return y

def rs_generator_poly(nsym):
    g = [1]
    for i in range(0, nsym):
        g = gf_poly_mul(g, [1, gf_exp[i+DATAMATRIX_GEN_BASE]])
    return g

def rs_encode_msg(msg_in, nsym):
    if len(msg_in) + nsym > 255:
        raise ValueError("message too long")
    gen = rs_generator_poly(nsym)
    msg_out = bytearray(len(msg_in) + nsym)
    msg_out[:len(msg_in)] = msg_in
    for i in range(0, len(msg_in)):
        coef = msg_out[i]
        if coef != 0:
            for j in range(0, len(gen)):
                msg_out[i + j] ^= gf_mul(gen[j], coef)
    msg_out[:len(msg_in)] = msg_in
    return msg_out

def rs_calc_syndromes(msg, nsym):
    return [gf_poly_eval(msg, gf_exp[i+DATAMATRIX_GEN_BASE]) for i in range(nsym)]

def rs_correct_errata(msg, synd, pos):
    # calculate error locator polynomial
    q = [1]
    for i in range(0, len(pos)):
        x = gf_exp[len(msg) - 1 - pos[i]]
        q = gf_poly_mul(q, [x, 1])
    # calculate error evaluator polynomial
    p = synd[0:len(pos)]
    p.reverse()
    p = gf_poly_mul(p, q)
    p = p[len(p) - len(pos):len(p)]
    # formal derivative of error locator eliminates even terms
    q = q[len(q) & 1:len(q):2]
    # compute corrections
    for i in range(0, len(pos)):
        x = gf_exp[pos[i] + 256 - len(msg)]
        y = gf_poly_eval(p, x)
        z = gf_poly_eval(q, gf_mul(x, x))

        adj = gf_div(y, gf_mul(x, z))
        if DATAMATRIX_GEN_BASE != 0:
            adj = gf_mul(adj, x)
        msg[pos[i]] ^= adj



def rs_find_errors(synd, nmess):
    # find error locator polynomial with Berlekamp-Massey algorithm
    err_poly = [1]
    old_poly = [1]
    for i in range(0, len(synd)):
        old_poly.append(0)
        delta = synd[i]
        for j in range(1, len(err_poly)):
            delta ^= gf_mul(err_poly[len(err_poly) - 1 - j], synd[i - j])
        if delta != 0:
            if len(old_poly) > len(err_poly):
                new_poly = gf_poly_scale(old_poly, delta)
                old_poly = gf_poly_scale(err_poly, gf_div(1, delta))
                err_poly = new_poly
            err_poly = gf_poly_add(err_poly, gf_poly_scale(old_poly, delta))

    errs = len(err_poly) - 1
    if errs * 2 > len(synd):
        raise ReedSolomonError("Too many errors to correct")

    # find zeros of error polynomial
    err_pos = []
    for i in range(0, nmess):
        if gf_poly_eval(err_poly, gf_exp[255 - i]) == 0:
            err_pos.append(nmess - 1 - i)
    if len(err_pos) != errs:
        return None    # couldn't find error locations
    return err_pos

def rs_forney_syndromes(synd, pos, nmess):
    fsynd = list(synd)      # make a copy
    for i in range(0, len(pos)):
        x = gf_exp[nmess - 1 - pos[i]]
        for i in range(0, len(fsynd) - 1):
            fsynd[i] = gf_mul(fsynd[i], x) ^ fsynd[i + 1]
        fsynd.pop()
    return fsynd

def rs_correct_msg(msg_in, nsym):
    if len(msg_in) > 255:
        raise ValueError("message too long")
    msg_out = list(msg_in)     # copy of message
    # find erasures
    erase_pos = []
    for i in range(0, len(msg_out)):
        if msg_out[i] < 0:
            msg_out[i] = 0
            erase_pos.append(i)

    if len(erase_pos) > nsym:

        raise ReedSolomonError("Too many erasures to correct")

    synd = rs_calc_syndromes(msg_out, nsym)
    if max(synd) == 0:
        return msg_out[:-nsym]  # no errors

    fsynd = rs_forney_syndromes(synd, erase_pos, len(msg_out))
    err_pos = rs_find_errors(fsynd, len(msg_out))
    if err_pos is None:
        raise ReedSolomonError("Could not locate error")

    rs_correct_errata(msg_out, synd, erase_pos + err_pos)
    synd = rs_calc_syndromes(msg_out, nsym)
    if max(synd) > 0:
        raise ReedSolomonError("Could not correct message")
    return msg_out[:-nsym]