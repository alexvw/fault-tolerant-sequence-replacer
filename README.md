# fault-tolerant-sequence-replacer
Swap frames from long videos without ever losing progress, regardless of errors

### Usage
python combine.py videoname.mp4

Have replacement frames in same folder, named 00001.png etc where the number matches the frame they replace. Will resume progress after fail every 1000 frames (configurable)

writes progress to frames and videos txt. Output will be output.mp4
