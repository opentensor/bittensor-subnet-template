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

4) Install docker on both machines, and make sure docker is running.
5) Install git and clone subnet repo on both machines.
5) Init docker swarm on first one, and join the swarm on the second one:
 
    ``docker swarm init``