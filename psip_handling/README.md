# setup

install all files of this directory in /usr/local/sbin

set crontab to:

```
0 4 * * *	/usr/local/sbin/psipcheck
0 10 * * * /usr/local/sbin/spacecheck
```

set up the folders noted in psipcheck (as of 2016-06-23):

```perl
# Define folders to search for updated XML files
my $debug			= 1;
my(@psips)		= (
[ "psipcunytv", "/SFTP_CUNY/psip/uploads/CUNYTV/" ],
[ "psipnycmg", "/SFTP_CUNY/psip/uploads/NYCMG/" ]
);

my($condir)		= "/SFTP_CUNY/psip/CONSOLIDATED/";
my($confile)	= "CUNYTV_PSIP_merged.xml";
my($schema)		= "/usr/local/sbin/pmcp31.xsd";
my($xsltfile)	= "/usr/local/sbin/psipmerger.xsl";
my($tmpfile)	= "/var/tmp/CUNYTV_PSIP_merged.xml";
my($mailbody)	= "";
my($ds)				= `date +%Y-%m-%d_%H-%M-%S`;
my($starttime)	= `date`;
chomp($starttime);
my($ffound)		= 0;
my($error)		= 0;
```

So pcmp files may be delivered to `/SFTP_CUNY/psip/uploads/CUNYTV/` and `/SFTP_CUNY/psip/uploads/NYCMG/` and then a merged output will be sent to `/SFTP_CUNY/psip/CONSOLIDATED/`.

This is currently setup at `ssh admin@192.168.30.23`.

Note there are two automated tasks scheduled here:

1. cron running psipcheck
2. On PSIP-1 the Task Manager is set up to copy the output of psipcheck to a local directory. On PSIP-1, this step is accessible in Task Manager, under Task Scheduler (Local), select "Task Scheduler Library" and see the task called XML Download.
