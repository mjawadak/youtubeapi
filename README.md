# From Network Traffic Measurements to QoE for Internet Video, IFIP 2019.

## The QoS-QoE dataset
The final structured dataset for ML modeling can be downloaded from https://drive.google.com/open?id=1MTmvOuKBE85XFyYQJBrABd2K-OOcwwVi

## For the code
Dependencies: pymongo,sklearn,dpkt,dnspython

Download the video catalog required by main.py from https://drive.google.com/open?id=1kcrLUk5t_8Rg0EqxN0erxOT-2QM3LhZ9

The mainController is implemented using main.py. It stores the results in MongoDB.

The clients are implemented using clientController.py

The stats from the pcap traces are obtained using readPcap.py

The ClfClass.py contains the code for the trace based sampling method based on the cell_distributionALL.csv file.

Root access is required on the linux machines since tcpdump is used to capture the network traffic.

The client is run with a google chrome extension. The extension ID needs to be modified in the clientController.py file.

The public IP and port of the mainController needs to be set in clientController.py

## For offline calculation of ITU MOS

For ITU MOS, we used the code provided in https://github.com/itu-p1203/itu-p1203. 

Use ituTest.py file to obtain the ITU MOS values from the mongoDB database collected using main.py offline.
