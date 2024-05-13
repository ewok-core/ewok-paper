#!/usr/bin/env bash
set -x
wget https://github.com/jspsych/jsPsych/releases/download/jspsych%407.3.2/jspsych.zip -P ./static/
unzip static/jspsych.zip -d static/jspsych
