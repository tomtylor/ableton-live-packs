#!/usr/bin/perl

use strict;
use warnings;

use WWW::Mechanize;
use Crypt::SSLeay;
use IO::Socket::SSL;
use Mozilla::CA;
use IPC::System::Simple qw(capture);

use Data::Dumper;
use File::stat;

my $mech = WWW::Mechanize->new();
$mech->get('https://www.ableton.com/en/login/');

my ($login, $password);
print "login: ";
chop($login=<STDIN>);
print "Password: ";
system('stty', '-echo');
chop($password=<STDIN>);
system('stty', 'echo');

$mech->submit_form(
    with_fields => {
        username    => $login,
        password    => $password,
    }
);
$mech->agent("Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2.18) Gecko/20110614 Firefox/3.6.18" );

my $alp;
my $category;
my (%hash, %hash_packs);
my $i = 0;

my $dmsurl = [ 'https://www.ableton.com/en/account/', 'https://www.ableton.com/en/packs/' ];

foreach my $url (@$dmsurl) {
    $mech->get($url);
    my @urlsource = $mech->links();
    foreach my $member ( \@urlsource ) {
        foreach my $data ( @{$member} ) {
            my $link = $data->[5]->{'href'};
            next if(!$link);
            if($link =~ /http:\/\/cdn.+\.alp/i) {
                $category = $link;
                $category =~ /\/livepacks\/(.*?)\//;
                $category = $1;
                $alp = $link;
                $alp =~ /([a-zA-Z0-9_\.\-]+\.alp)/;
                $alp = $1;
                $hash{$link} = $category;
                $hash_packs{$alp} = 1;
                $i++;
            }
        }
    }
}

print Dumper \%hash;
print Dumper \%hash_packs;
exit;

my $pack_count = 0;
my $dir = '/home/tk5149/AbletonLivePacks/';
print "Changing folder to $dir\n";
chdir($dir) or die "$!";

foreach my $element (keys %hash) {
    my $pack_name = $element;
    $pack_name =~ /([A-Za-z0-9\-_\.]+\.alp)/ig;
    $pack_name = $1;
    
    my $URL = $element;
    $URL =~ s/\s&\s/%20&%20/ig;
    
    my $file_info = capture("curl -sI '$URL'");
    $file_info =~ /Content-Length: ([0-9]+)/;
    $file_info = $1;
    

    die 'Something wrong with pack name' unless $pack_name =~ /^[A-Z0-9].+\.alp$/;
    # print "$hash{$element} => $pack_name => $element\n";
    $pack_count++;

    if (-e $dir.$hash{$element}.'/'.$pack_name) {
        my $filesize = stat("$dir$hash{$element}/$pack_name")->size;
        if($file_info != $filesize) {
            print "Disk size: $filesize != real size: $file_info\n";
            sleep(2);
            if (not -d "$hash{$element}") {
                print "Creating folder '$hash{$element}'\n";
                system `mkdir -p '$hash{$element}'`;    
            }
            print "Downloading $element\n";
            # system `curl -O -# '$URL'`;
            print "Moving $pack_name to '$hash{$element}'\n";
            # system `mv $pack_name '$hash{$element}'`;
        }
        else {
            print "File $dir$hash{$element}/$pack_name Exists! Skipping...\n";
            next;
        }

    }
    else {
        next if($file_info > 104857600);
        if (not-d "$hash{$element}") {
            print "Creating folder '$hash{$element}'\n";
            system `mkdir -p '$hash{$element}'`;
        }
        print "Downloading $element\n";
        system `curl -O -# '$URL'`;
        print "Moving $pack_name to '$hash{$element}'\n";
        system `mv $pack_name '$hash{$element}'`;  
    }
}
print "\n\n##########################\n|";
print "   $pack_count packs in total    ";
print "|\n##########################\n\n";

exit;
