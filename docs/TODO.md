# TO DO List

## Within PRJDATA.ZDT File

* [ ] Display the MASTER audio file.
* [ ] The FADER level for the MASTER track.
* [ ] How Invert is represented.
* [ ] How Stereo Link is represented.

## Within EFXDATA.ZDT File

* [ ] Whether an INSERT EFFECT is associated with the Master.
* [x] Current settings for REVERB (on/off, patch number, patch name)
* [x] Current settings for CHORUS (on/off, patch number, patch name)
* [ ] Whether an INSERT EFFECT is associated with a TRACK (as INPUT SOURCE). (What would we do if it was associated with INPUT?)

## Outside of PRJDATA.ZDT File

* [x] Parse entire Project directory to get project number.
* [x] Parse entire Project directory to get list of all AUDIO files. Use it to find *EXTRA* files not assigned to tracks.
* [x] Load all "bars_used" settings for each track.
* [x] May need to parse the `EFXDATA.ZDT` file for INSERT EFFECT values.

## Within the TEMPLATE HTML File

* [ ] Values for MASTER need to have field names
* [x] How to show unassigned files?
* [ ] Should we show values for all columns? Can we find more space?
* [ ] Add some place to show the current date? Maybe an optional note from the caller?