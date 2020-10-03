#!/bin/bash

if [ -z $(ps -A | grep fswebcam) ] ; then
	fswebcam -r "800x600" $1
	cp $1 /home/pi/Pictures/image.jpg
fi


