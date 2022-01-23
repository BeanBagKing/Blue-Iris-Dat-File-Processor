# About
Processes unsuccessful Blue Iris / DeepStack analysis (dat) files.
This is still (and will likely remain) a very rough script. It currently works for me, and I am thus unlikely to make any significant improvements to it

This script will proccess DeepStack analysis files and extract images from those with failed (error 100) or no successful message. It then runs the extracted images back through DeepStack to find items that may have been missed.

# Requirements
- ffmpeg, python3, DeepStack AI
- I'm using this in WLS (Windows Subsystem for Linux) on the same system as my Blue Iris/DeepStack install. If you are using this elsewhere, you may have to adjust script arguments, API calls, or have additional requirements.

Change the three *_folder locations at the top of the script to match your environment. Create the temp and review folders.

# Walkthrough
- Create a "bookmark" file with a timestamp so the script can resume from a location without having to re-process every file
- Start walking new files, looking for any dat file that either
  - Has a "error 100" (timeout) failure or
  - Has no successful messages
- Upon finding one, extracts the images from the file
- Performs DeepStack analys on each images
  - Enriches the results somewhat, tagging metadata with average score, person found, etc.
- Attempts to select the best single image
  - Looks for items that meet confirm models and do not have cancel models and meet the minimum confidence
  - Looks for people images first, selecting the highest confidence from those
  - If no people, looks for the highest average confidence
  - If there are ties, just grabs the first one
- Starts processing the next file

# FAQ
- Dude... your code... https://xkcd.com/1513/
  - It works
- Why did you do X the way you did?
  - I'm not a programmer by trade. I know enough to quickly throw together things that solve a problem I'm having. That's what was done here. If you're headscratching at the methods I used, then there's probably not a real reason behind it except that it's the fastest way I knew of to make it do what I wanted.
- Will you add feature Y?
  - Probably not. Like I said, I'm not a programmer and don't have the desire to spend my time adding features and fixing issues. I do think others could benifit from this though. It might also inspire someone to make a background service that does a proper job of this too.
- Why are there so many print statements?
  - Those are there from debugging issues. It's more work to remove them than leave them in, so they are still there. Feel free to remove them.
