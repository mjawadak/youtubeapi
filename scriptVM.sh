#!/usr/bin/expect -f

spawn ssh inria_r2lab.tutorial@faraday.inria.fr
set arg [lindex $argv 0]
expect "\$" {
send -- "ssh root@$arg\r"
}
expect # {
send -- "cd /root/Downloads/randomCollectionYouTubeR2Lab/\r"
send -- "./startClientYT.sh 35.180.61.99\r"
}

interact
