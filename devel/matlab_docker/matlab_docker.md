# Creating a docker image with matlab for kilosort

The goal here is to get a matlab docker image that has the necessary toolboxes to run kilosort. In order to run matlab within the container, you'll need to provide license information. That's a separate issue.

First build the matlab_docker1 image (see the docker1 subdirectory)

Then:

```bash
docker run -it --rm matlab_docker1
```

Enter your matlab user name and password to start matlab.

Copy the credentials that are inside the container (from a new terminal):

```bash
docker cp <container-id>:/root/.matlab/MathWorks/MATLAB/LNUCredentials/LNUCreds.info $HOME/container_LNUCreds.info
```

where `<container-id>` is the ID of the docker container you are running

Exit the docker image, and restart via:

```bash
xhost +
docker run -it --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro --shm-size=512M -v $HOME/container_LNUCreds.info:/root/.matlab/MathWorks/MATLAB/LNUCredentials/LNUCreds.info matlab_docker1 bash
```

Then inside the container run

```
matlab
```

Now you shouldn't need to enter your credentials, and you should get a graphical matlab session! Importantly, however, your credentials are not actually stored in the docker image.

From the GUI click Add-Ons -> Get Add-Ons

Install the required toolboxes. For kilosort, that would be: parallel computing toolbox, signal processing toolbox, Statistics and Machine Learning Toolbox.

I think you may need to install them one at a time.

Then close matlab withing the container (but keep the container running) and commit the image:

```bash
docker commit <container-id> magland/docker_for_kilosort:0.1.0
```

Now try to create a new container with the committed image:

```bash
docker run -it magland/docker_for_kilosort:0.1.0 bash
```

Then run `matlab` inside that new container. It should ask for the user name and password. And you should have the toolboxes installed! To check this, type `ver` in matlab, and you should see something like:

```
>> ver
-----------------------------------------------------------------------------------------------------
MATLAB Version: 9.9.0.1592791 (R2020b) Update 5
MATLAB License Number: 40764494
Operating System: Linux 5.4.0-70-generic #78~18.04.1-Ubuntu SMP Sat Mar 20 14:10:07 UTC 2021 x86_64
Java Version: Java 1.8.0_202-b08 with Oracle Corporation Java HotSpot(TM) 64-Bit Server VM mixed mode
-----------------------------------------------------------------------------------------------------
MATLAB                                                Version 9.9         (R2020b)
Parallel Computing Toolbox                            Version 7.3         (R2020b)
Signal Processing Toolbox                             Version 8.5         (R2020b)
Statistics and Machine Learning Toolbox               Version 12.0        (R2020b)
```

Finally, push to dockerhub

```bash
docker push magland/matlab_for_kilosort:0.1.0
```