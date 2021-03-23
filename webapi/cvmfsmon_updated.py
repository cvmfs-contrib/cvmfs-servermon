import sys
import datetime, dateutil.parser, dateutil.tz

# common timezones as defined at https://stackoverflow.com/a/4766400
tz_str = '''-12 Y
-11 X NUT SST
-10 W CKT HAST HST TAHT TKT
-9 V AKST GAMT GIT HADT HNY
-8 U AKDT CIST HAY HNP PST PT
-7 T HAP HNR MST PDT
-6 S CST EAST GALT HAR HNC MDT
-5 R CDT COT EASST ECT EST ET HAC HNE PET
-4 Q AST BOT CLT COST EDT FKT GYT HAE HNA PYT
-3 P ADT ART BRT CLST FKST GFT HAA PMST PYST SRT UYT WGT
-2 O BRST FNT PMDT UYST WGST
-1 N AZOT CVT EGT
0 Z EGST GMT UTC WET WT
1 A CET DFT WAT WEDT WEST
2 B CAT CEDT CEST EET SAST WAST
3 C EAT EEDT EEST IDT MSK
4 D AMT AZT GET GST KUYT MSD MUT RET SAMT SCT
5 E AMST AQTT AZST HMT MAWT MVT PKT TFT TJT TMT UZT YEKT
6 F ALMT BIOT BTT IOT KGT NOVT OMST YEKST
7 G CXT DAVT HOVT ICT KRAT NOVST OMSST THA WIB
8 H ACT AWST BDT BNT CAST HKT IRKT KRAST MYT PHT SGT ULAT WITA WST
9 I AWDT IRKST JST KST PWT TLT WDT WIT YAKT
10 K AEST ChST PGT VLAT YAKST YAPT
11 L AEDT LHDT MAGT NCT PONT SBT VLAST VUT
12 M ANAST ANAT FJT GILT MAGST MHT NZST PETST PETT TVT WFT
13 FJST NZDT
11.5 NFT
10.5 ACDT LHST
9.5 ACST
6.5 CCT MMT
5.75 NPT
5.5 SLT
4.5 AFT IRDT
3.5 IRST
-2.5 HAT NDT
-3.5 HNT NST NT
-4.5 HLV VET
-9.5 MART MIT'''

tzd = {}
for tz_descr in map(str.split, tz_str.split('\n')):
    tz_offset = int(float(tz_descr[0]) * 3600)
    for tz_code in tz_descr[1:]:
        tzd[tz_code] = tz_offset

def runtest(repo, limits, repo_status, errormsg):
    testname = 'updated'

    warning_hours = limits[testname + '-warning']
    critical_hours = limits[testname + '-critical']

    msg = ''
    multiplier = 1
    if errormsg != "":
        if not errormsg.endswith('Not found'):
            return [ testname, repo, 'CRITICAL', 'error: ' + errormsg]
        # else Not found, treat it as initial snapshot in progress
    if 'last_snapshot' in repo_status:
        lastdate_string = repo_status['last_snapshot']
        if lastdate_string == '':
          return [ testname, repo, 'CRITICAL', 'error: empty snapshot date' ]
        try:
	    # tzinfos not needed because this is always UTC
            lastdate = dateutil.parser.parse(lastdate_string)
        except:
            msg =  str(str(sys.exc_info()[1]))
            return [ testname, repo, 'CRITICAL', 'error parsing last_snapshot date: ' + msg]
    else:
        # no 'last_snapshot' found in .cvmfs_status.json
        if 'snapshotting_since' not in repo_status:
            return [ testname, repo, 'WARNING', 'initial snapshot not in progress' ]
        lastdate_string = repo_status['snapshotting_since']
        if lastdate_string == '':
          return [ testname, repo, 'CRITICAL', 'error: empty .cvmfs_is_snapshotting' ]
        try:
            lastdate = dateutil.parser.parse(lastdate_string, tzinfos=tzd)
        except:
            msg =  str(str(sys.exc_info()[1]))
            return [ testname, repo, 'CRITICAL', 'error parsing .cvmfs_is_snapshotting date: ' + msg]

        msg = 'initial snapshot started'
        # turn 8 hours into 3 days and 24 hours into 9 days
        multiplier = 9

    now = datetime.datetime.now(dateutil.tz.tzutc())
    try:
      delta = now - lastdate
    except:
      return [ testname, repo, 'CRITICAL', 'error subtracting ' + str(lastdate) + ' from ' + str(now) ]
    diff_hours = (delta.days * 24) + int(delta.seconds / 3600)

    if diff_hours < (warning_hours * multiplier):
        status = 'OK'
    elif diff_hours < (critical_hours * multiplier):
        status = 'WARNING'
    else:
        status = 'CRITICAL'

    if status != 'OK':
        if msg == '':
            msg = 'last successful snapshot'
        msg += ' ' + str(diff_hours) + ' hours ago'

    return [ testname, repo, status, msg ]
