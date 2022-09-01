#!/bin/sh
convert -colorspace Gray $1 movie_grayscale/$(basename $1)
