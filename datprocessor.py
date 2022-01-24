#!/usr/bin/python3

import os, re, shutil, requests, os, math, time, glob, ntpath, subprocess, random

alerts_folder = "/mnt/c/BlueIris/Alerts/"
#alerts_folder = "/mnt/c/Users/Administrator/Desktop/all_error_dat_files/"
#alerts_folder = "/mnt/c/Users/Administrator/Desktop/testing/"
temp_folder = "/mnt/c/Users/Administrator/Documents/temp/"
results_folder = "/mnt/c/Users/Administrator/Documents/review/"

to_confirm = ['person','bicycle','car','motorcycle','bus','truck','bird','cat','dog','bear','deer','rabbit','raccoon','fox','skunk','squirrel']
to_cancel = ['BobRoss']
custom_models = 'objects:0,combined'
mark_as_vehicle = 'car,truck,bus,vehicle'
min_confidence = 60

def get_dat_files():
    try:
        with open(alerts_folder+'bookmark.txt', "r") as bookmark:
            lastchecked = bookmark.read()
            try:
                lastchecked = float(lastchecked)
            except:
                lastchecked = 0
            bookmark.close()
    except:
        with open(alerts_folder+'bookmark.txt', "w") as bookmark:
            bookmark.write("0")
            lastchecked=0
            bookmark.close()

    try:
        print("start 1")
        #files = [f for f in os.listdir(alerts_folder) if os.path.isfile(f)]
        files = glob.glob(os.path.expanduser(alerts_folder+"*.dat"))
        #sorted_by_mtime_descending = sorted(files, key=lambda t: -os.stat(t).st_mtime)
        sorted_by_mtime_ascending = sorted(files, key=lambda t: os.stat(t).st_mtime)
        print("start 2")
    except:
        print("file probably got deleted, retrying")
        get_dat_files()

    for file in sorted_by_mtime_ascending:
        #print(file)
        #print(str(os.path.getmtime(file)) + " > " + str(lastchecked) + " " + str(os.path.getmtime(file) > float(lastchecked)))
        try:
            if (os.path.getmtime(file) > float(lastchecked)):
                if check_dat_file(file):
                    shutil.copy(file, temp_folder)
                    extract_images(ntpath.basename(file))
                    print("CHECKED")
            if os.path.getmtime(file) > lastchecked:
                lastchecked = os.path.getmtime(file)
            with open(alerts_folder+'bookmark.txt', "w") as bookmark:
                bookmark.write(str(lastchecked))
                bookmark.close()
        except:
            print("no such file or directory, retrying")
            get_dat_files() 

def check_dat_file(file):
    f = open(file, "rb")
    byte = f.read()
    sendit = False
    error_pattern = b'\x45\x00\x72\x00\x72\x00\x6F\x00\x72\x00\x20\x00\x31\x00\x30\x00\x30' # E.r.r.o.r. .1.0.0
    success_pattern = b'\x73\x00\x75\x00\x63\x00\x63\x00\x65\x00\x73\x00\x73' # s.u.c.c.e.s.s

    test = byte.find(error_pattern)
    if test != -1: # not -1 means something (error) was found, send all of thse
        sendit = True
    if not sendit:
        test = byte.find(success_pattern)
        if test == -1: # -1 means nothing (no success) was found, even if no error was found, if there wasn't a success, send it
            sendit = True
    f.close()
    return sendit

def extract_images(file):
    file = temp_folder+file
    timestamp=str(int(time.time()))
    jpg_file_name = temp_folder+ntpath.basename(file)+"_%05d.jpg"
    subprocess.call(['ffmpeg', '-i', file, jpg_file_name],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #cmd=str("ffmpeg -i "+file+" " +temp_folder+"out_"+timestamp+"_%05d.jpg")
    #os.system(cmd)
    os.remove(file)
    test_images()

def test_images():
    file_detection = []
    files = glob.glob(temp_folder+"*.jpg")
    for file in files:
        temp_dict = {}
        confidencemax = 0
        image_data = open(file,"rb").read()
        try:
            response = requests.post("http://blueiris.nullsec.link:82/v1/vision/detection",files={"image":image_data},timeout=15).json()
            if response['success'] != True:
                print("Non successful response. Response below. Sleeping 10 and retrying")
                print(response)
                time.sleep(10)
                get_dat_files()
        #{'success': True, 'predictions': [{'confidence': 0.8149414, 'label': 'car', 'y_min': 77, 'x_min': 2, 'y_max': 178, 'x_max': 111}], 'duration': 0}
        except:
            print("An error has occured. Sleeping 10 and retrying")
            time.sleep(10)
            get_dat_files()
        items = len(response['predictions'])
        if items == 0:
            os.remove(file)
        if items != 0:
            temp_dict["filename"]=str(ntpath.basename(file))
            for item in range(items):
                label = str(response['predictions'][item]['label'])
                confidence = int(math.ceil(response['predictions'][item]['confidence']*100))
                temp_dict[label]=confidence
            file_detection.append(temp_dict)
    print("FIN")
    select_image(file_detection)

def select_image(file_detection):
    # Lets start enriching
    person_list=[]
    items_list=[]
    max_avg=0
    max_per=0
    print(file_detection)
    for item in file_detection:

        # Add an average
        filtered_vals = [v for _, v in item.items() if v != 0 and type(v) == int]
        average = sum(filtered_vals) / len(filtered_vals)
        item["avg"]=round(average,2)

        # Do we see anything on our confirm list?
        for confirm in to_confirm:
            if confirm in item:
                item["confirm"]=True
                break # We found it, we're done here

        # Do we see anything on our cancel list?
        for cancel in to_cancel:
            if cancel in item:
                item["cancel"]=True
                break # We found it, we're done here

        # Are all detections above our minimum confidence?
        for value in item.values():
            if type(value) == int:
                if value >= min_confidence:
                    item["min_confidence"]=True
                    break
        print(item)

    # Seems friggin stupid, but if we all the steps in one for loop
    # then the list size cahnges and we drop the wrong thing.
    for item in file_detection: # enrichment done
        if "cancel" in item:
            pass # Toss it all, end of discussion
        else: 
            if "confirm" not in item:
                pass # There's nothing here we're interested in, don't process further
            else:
                if "min_confidence" not in item:
                    pass # We're not confident enough to do anything, don't process further
                else:
                    if "person" in item:
                        item["contains_person"]=True
                        person_list.append(item) # Add it to our special list
                    else:
                        items_list.append(item) # It's not a person, but we're still interested, add it to a new list

    # Our list is now enriched and any items not meeting criteria have been dropped

    #shutil.copy(temp_folder+item['filename'], results_folder)
    #os.remove(temp_folder+item['filename'])

    print(person_list)

    #print(items_list)
    if len(person_list) > 0: # There are people, we're going to select one of these
        print("there's people")
        for item in person_list:
            if max_avg < item['avg']: # This variable we may not end up using, but would give us the highest average confidence
                max_avg = item['avg']
            if max_per < item['person']: # This variable we may not end up using, but would give us the highest confidence person
                max_per = item['person']

        if len(person_list) > 1: # If there is more than one item in the person list, we're going to get the highest confidence person
            get_max_per = [d for d in person_list if d['person'] == max_per]
            if len(get_max_per) > 1: # If there are more than 1 image with the highest confidence person, we're going to get the highest average
                get_max_avg = [d for d in person_list if d['avg'] == max_avg]
                if len(get_max_avg) > 1: #If we're STILL tied, screw it, we're grabbing something at random
                    rand = random.choice(get_max_per)
                    print("Person Selected via Random")
                    print(rand)
                    shutil.copy(temp_folder+rand['filename'], results_folder)
                else:
                    print("Person Selected via High Average")
                    print(get_max_avg[0])
                    shutil.copy(temp_folder+get_max_avg[0]['filename'], results_folder)
        else:
            print("Person Selected via only one")
            print(person_list[0])
            shutil.copy(temp_folder+person_list[0]['filename'], results_folder)


        #print(person_list)
        #get_max_avg = [d for d in person_list if d['avg'] == max_avg]
        #get_max_per = [d for d in get_max_avg if d['person'] == max_per]
        #print(str(dict(get_max_per[0])['filename'])) ## failing no list
        #shutil.copy(file, temp_folder)
    elif len(items_list) == 0:
        print("absolutly nothing left")

    else: # There are no people, so we'll take what we can get
        print("No People, slecting first image with highest average")
        for item in items_list:
            if max_avg < item['avg']: # This variable we may not end up using, but would give us the highest average confidence
                max_avg = item['avg']
        #for f in items_list:
        #    print(f)
        print(max_avg)
        get_max_avg = [d for d in items_list if d['avg'] == max_avg]
        print(get_max_avg)
        print(get_max_avg[0]['filename'])
        shutil.copy(temp_folder+get_max_avg[0]['filename'], results_folder)

    print("cleaning whats left in directory")
    for f in os.listdir(temp_folder):
        os.remove(os.path.join(temp_folder, f))


get_dat_files()
