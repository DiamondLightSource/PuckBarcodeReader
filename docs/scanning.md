Continuous Barcode Scanning
===========================
The barcode scanner can be used to scan a puck from an image file, however the major intended use case is to have the scanner continuously taking image frames from an attached webcam.

Data Flow Between Processes
---------------------------
The Camera Scanner starts two sub-processes: the capture process and the scanner process. Below is a schematic of the overall data flow between processes.

![](img/CameraDataFlow.png)


