## Purchasing Machines

1) Create account at Scaleway.com, complete KYC process.
2) Create your ssh on the machine which will be used to access scaleway machines.
3) Create 2 elastic server instance at scale way, choose Paris 1 and purchase 2 machines:
- **(A)** EM-B212X-SSD ( Intel Xeon E5 2620 or equivalent, RAM 256 GB, Disks 2 x 1 TB SSD )
- **(B)** EM-B112X-SSD ( Intel Xeon E5 2620 or equivalent, RAM
192 GB, Disks
2 x 1 TB SSD )

    First server will be used to run memgraph, indexer, miner, and the second one to run bitcoin core node;
While purchasing machines, select private network integration, so the machines can communicate each other via private network.


4) Install python on both machines
 - ``sudo apt-get install python3.9``
 - ``alias python=python3``
 - ``source ~/.bashrc``
 - ``python --version``

4) Install docker on both machines, and make sure docker is running.
- ``apt-get install docker``
- ``apt-get install docker-compose``
5) clone subnet repo on both machines:``git clone https://github.com/blockchain-insights/blockchain-data-subnet.git``

Task: Provide readme.md for
NODE
sudo ip link add link eno1 name eno1.2733 type vlan id 2733
sudo ip link set eno1.2733 up
sudo ip addr add 172.16.4.2/22 dev eno1.2733


MINER
sudo ip link add link eno1 name eno1.3530 type vlan id 3530
sudo ip link set eno1.3530 up
sudo ip addr add 172.16.4.3/22 dev eno1.3530


on node machine
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8333 comment 'Allow Bitcoin Node'
sudo ufw allow 8332 comment 'Allow Bitcoin RPC'

sudo ufw allow 8333/tcp comment 'Allow Bitcoin Node'

for .env file use docker eth ip address

 sudo ufw status
sudo ufw reload


8) install python 3.9 on both machines

