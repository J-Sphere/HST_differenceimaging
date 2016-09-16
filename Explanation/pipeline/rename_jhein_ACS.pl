#!/usr/bin/env perl

#Original in cdperl// HSTWFC3UVIS_jhein/rename_jhein.pl
push(@INC, $ENV{"PIPE_PERL"});
require "genericprocs.pl";
require "config.pl";
use Cwd 'abs_path';
&GetParameter($parameterfilename);
require "getphotcodes4images.pl";

$dir = ".";
$onlyshow=0;
$fieldmappingstring = "";
$cpflag=0;
$skipbad=0;
$defaultfield="";

my (@options) = @ARGV;
my $i = 0;

do {
    $i_save=$i;
    if ($options[$i] eq "-dir")             {$dir=$options[++$i];$i++;}
    if ($options[$i] eq "-onlyshow")        {$onlyshow=1;$i++;}
    if ($options[$i] eq "-fieldmapping")    {$fieldmappingstring=$options[++$i]; $i++;}
    if ($options[$i] eq "-skipbad")         {$skipbad=1;$i++;}
    if ($options[$i] eq "-copy")            {$cpflag=1;$i++;}
    if ($options[$i] eq "-defaultfield")    {$defaultfield=$options[++$i];$i++;}

    if ($options[$i] eq "-h")               {
	print STDERR "USAGE: renameHST30DOR.pl [-dir directory][-onlyshow][-fieldmapping mapping][-skipbad][-cpflag][-defaultfield fieldname]\n";
	print STDERR "if -onlyshow, then the rename commands are only shown, but not executed\n";
	print STDERR "define a mapping of fieldnames (comma-separated list), e.g. -fieldmapping 'eta->EtaCarina,ogle->ogle-375'\n";
	exit(0);
    }
    if ($i_save==$i) {
	if ($options[$i] eq ""){
	    $i++;
	} else {
	    print STDERR "ERROR stage.pl: wrong flag: <$options[$i]>, exiting...\n";exit(0);
	}
    }
} while ($i < @options);

undef my %fieldhash;
if ($fieldmappingstring ne ""){    
    my @fieldmappings = split(/,/,$fieldmappingstring);
    foreach $fieldmapping (@fieldmappings){
	($field,$fieldnew) = $fieldmapping =~ /(.*)->(.*)/;
	$fieldhash{$field}=$fieldnew;
    }
}

$dir = abs_path($dir);
print STDERR "indir: $dir\n";

my $outrootdir = $RAWDATA_DIR;
my $outrootdir2 = $WORKSPACE_DIR;
print STDERR "outrootdir: $outrootdir\n";

my @files = `ls $dir/*.fits`;
chomp(@files);

undef my %fileinfo;
undef my %badfiles;
undef my @warnings;
undef my %summary;

@skipnames = split(/,/,$SKIPNAMES);

my $counter=1;
#print $files;
foreach my $file (@files){
    my ($errorflag,$target,$filter,$instrument,$detector,$propid,$dateobs,$timeobs, $fcnum, $diffval, $ccdchip, $survey) = &GetFitsKeywords($file,"TARGNAME","FILTER","INSTRUME","DETECTOR","PROPOSID","DATE-OBS","TIME-OBS", "FCNUM","DIFFVAL", "CCDCHIP", "SURVEY");
    if ($instrument ne "ACS"){
	my $warning = "WARNING!!!!! $file is not WC3, it is $instrument";
	print STDERR "$warning\n";
	push(@warnings,"$warning");
	next;
    }
    if ($detector ne "WFC"){
	my $warning = "WARNING!!!!! $file is not UVIS, it is $detector";
	print STDERR "$warning\n";
	push(@warnings,"$warning");
	next;
    }

    if ($errorflag){
	if ($skipbad){
	    my $warning = "WARNING!!!!! Could not read fitskeys from $file: ($errorflag,$target,$filter,$instrument,$propid) Skipping file...";
	    print STDERR "$warning\n";
	    push(@warnings,"$warning");
	    next;
	} else {
	    die "Could not read fitskeys from $file: ($errorflag,$exptype,$filter,$object)\n";
	}
    }
    ($mjd) = `getdate fd2mjd $dateobs\T$timeobs`;
    chomp($mjd);
    

    my $imagefilesize=filesize("$file");
    my $goodfilesizeflag=0;
    @goodfilesizes = split(/,/,$IMAGEFILESIZE);
    $goodfilesizeflag=1 if (scalar(@goodfilesizes)==0);
    foreach $goodfilesize (@goodfilesizes){
	# allow variation in the fits header length: +-2880
	$goodfilesizeflag=1 if ( ( $imagefilesize==$goodfilesize) ||
				 (($imagefilesize+2880)==$goodfilesize) ||
				 (($imagefilesize-2880)==$goodfilesize)    );
    }

    if (!$goodfilesizeflag){
	print STDERR "SKIPPING $file since filesize=$imagefilesize!=@goodfilesizes\n";
	next;	    
    }

    $field = $target;
    $field =~ s/^\s+|\s+$//g;
    $field =~ s/\s+/_/g;
    $field =~ s/[,.;+-]//g;
    if ($field eq ""){
	if ($defaultfield eq ""){
	    my $warning = "!!!WARNING!!!! image $file does not have a fieldname in OBJECT! skipping!!!";
	    print STDERR "$warning\n";
	    push(@warnings,"$warning");
	    next;
	} else {
	    my $warning = "!!!WARNING!!!! image $file does not have a fieldname in OBJECT! Setting it to default field name $defaultfield!!!";
	    print STDERR "$warning\n";
	    push(@warnings,"$warning");
	    $field=$defaultfield;
	}
    }
    my $skipflag=0;
    foreach my $skipname (@skipnames){
	if ($field eq $skipname){
	    my $skipmessage = "SKIP field=$skipname";
	    $badfiles{$file}= $skipmessage;
	    $skipflag=1;
	    last;
	}
    }
    if ($skipflag){
	next;
    }

    (my $file_short = $file) =~ s/.*\///;
    my ($suffix) = $file_short =~ /\_(\w+\.fits)$/;
    $file_short =~ s/\_\w+\.fits$//;

    $field = lc($field);
    $number=int($propid*1000+$counter);

    if ($fieldhash{$field} ne ""){
	$field = $fieldhash{$field};
    }
    

    my $newnameroot1 ="${field}.$propid.$instrument.$detector.$filter.$file_short\_$mjd";
    my $newnameroot2 ="${field}.$propid.$instrument.$detector.$filter.$file_short\_$mjd";
    #my $newoutdir1 = "$outrootdir/$survey/1";
    #my $newoutdir2 = "$outrootdir/$survey/2";
    
    if ($diffval eq "1"){

    $newoutdir1 = "$outrootdir/$survey\_$filter/1";
    $newoutdir2 = "$outrootdir/$survey\_$filter/2";

    } else {
    $newoutdir1 = "$outrootdir/$survey\_$filter\_tmpl/1";
    $newoutdir2 = "$outrootdir/$survey\_$filter\_tmpl/2";
    }

    if (!$onlyshow){
	if (!(-e $newoutdir1)) { !system ("mkdir -p $newoutdir1") || printf  ("$: $!\n"); }
	if (!(-e $newoutdir2)) { !system ("mkdir -p $newoutdir2") || printf  ("$: $!\n"); }
    }
    &newname2file("$newoutdir1/$newnameroot1\_$suffix",$file,$onlyshow,$cpflag);
    &newname2file("$newoutdir2/$newnameroot2\_$suffix",$file,$onlyshow,$cpflag);
    $counter++;
}

##### WARNINGS

if (scalar(@warnings)>0){
    print STDERR "\n####### THERE WERE WARNINGS!!!!!!!\n";
    foreach my $warning (@warnings){
	print STDERR "$warning\n";
    }
}

exit(0);

sub newname2file{
    my ($newname,$file,$onlyshow,$cpflag)=@_;

    ($newname_short = $newname) =~ s/.*\///;
    ($file_short = $file) =~ s/.*\///;
    if ($onlyshow){
	if ($cpflag){
	    print STDERR "showing: copying $file_short -> $newname_short\n";
	} else {
	    print STDERR "showing: linking $file_short -> $newname_short\n";
	}
    } else {
	&DeleteFile($newname);
	if (-e $newname){
	    print STDERR "ERROR: Could not delete $newname\n";
            exit(0);
	}
	if ($cpflag){
	    print STDERR "Copying $file_short -> $newname_short\n";
	    system("cp $file $newname");
	    if (!(-e $newname)){
		print STDERR "ERROR: Could not copy $file_short to $newname_short\n";
		exit(0);
	    }
	} else {
	    print STDERR "linking $file_short -> $newname_short\n";
	    &linkfiles($newname,$file,1); 
	    if (!(-l $newname)){
		print STDERR "ERROR: Could not move $file_short to $newname_short\n";
		exit(0);
	    }
	}
    }
}

# Link 
sub linkfiles{
    my ($link,$file2link,$exitflag)=@_;
    my $existinglink = readlink($link);
    $okflag=1;
    if ((!defined($existinglink)) || ($existinglink ne $file2link)){
	&DeleteFile($link);
	unless (symlink ($file2link, $link)) { 
	    bye ("cannot symlink $link to $file2link") if ($exitflag);
	    print STDERR "warning: cannot symlink $file2link to $link\n";
	    $okflag=0;
	}
    } else {
	$okflag=0;
    }
    return($okflag);
}
