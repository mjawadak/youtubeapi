# youtubeapi

A framework to collect YouTube QoS-QoE datasets by controlled experimentation.

QoS -> Network Quality of Service features e.g. bandwidth, delay, packet loss.

QoE -> The Quality of Experience for the given playout. The labels are based on application level measurements of join_time and stalling events.

The dataset can be downloaded from https://drive.google.com/open?id=1MTmvOuKBE85XFyYQJBrABd2K-OOcwwVi

Dependencies:
pymongo,sklearn,dpkt,dnspython

For ITU MOS, we used the code provided in https://github.com/itu-p1203/itu-p1203

The mainController is implemented using main.py. 

The clients are implemented using clientController.py

The stats from the pcap traces are obtained using readPcap.py

The ClfClass.py contains the code for the trace based sampling method based on the cell_distributionALL.csv file.

Root access is required on the linux machines since tcpdump is used to capture the network traffic.

The client is run with a google chrome extension. The extension ID needs to be modified in the clientController.py file.

The public IP and port of the mainController needs to be set in clientController.py
