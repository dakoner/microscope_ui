#!/bin/bash
source ~/.bashrc
source /home/dek/miniconda3/etc/profile.d/conda.sh
conda activate microscope
cd /home/dek/src/microscope_ui
python microscope_ui.py dekscope 5000
