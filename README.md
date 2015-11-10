# addr2func
Android memory leak analyse tool

The original code is forked from http://freepine.blogspot.ca/2010/02/analyze-memory-leak-of-android-native.html

I just modifed the script to support latest version of Android

*Below instruction is for debugging mediaserver
*You might need root permission

Build AOSP or your android source code.

$adb shell setprop libc.debug.malloc 1
$adb shell ps mediaserver
$adb shell kill <mediaserver_pid>
$adb shell ps mediaserver
$adb pull /proc/<mediaserver_pid>/maps
$adb shell dumpsys media.player -m > dump1
Do your test
$adb shell dumpsys media.player -m > dump2
$diff dump1 dump2 > diff
$./addr2func.py --root-dir=<AOSP_dir> --maps-file=maps --product=<product_name_of_your_build> diff > mem_trace

Now you can see the memory allocation trace in mem_trace file.
