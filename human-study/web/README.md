# jsPsych EWoK Experiment 

This directory defines and implements the jsPsych experiment for eliciting judgments from humans on things in a variety of formats (binary forced choice, likert, freeform text). 

- Static HTML web page with embedded scripts for handling experimental logic and saving results (DEFAULT). 

## templates/ewok.html

This file contains the meat of the experiment. This file defines the jsPsych instance, the timeline of experimental stimuli, and the functions that occur upon finishing the experiment. 

## static/

This directory contains static resources that are loaded by the HTML file. This includes jsPsych
library and plugins (JavaScript files in `jspsych/`), the experimental stimuli (JavaScript files in
`data/`), sound files (`chime.wav`), formatting files (`expt.css`), helper functions and
constants (`utils.js`), and a PHP file for saving results to the server (`write_data.php`).

## results/

This directory contains saved results from participants. Each session is associated with a random
32-character alphanumeric filename (excluding .csv extension) which is unlikely to be shared by any
other participant. 


## ack
many thanks to `thclark@mit.edu` for initial code 