#!/bin/bash
# Author - Václav Hrabě
printf "\nStart tester\n" 
  
data='data/test1/bbb'
seme='circles_graph.py'

printf "\nTest 1\n(Zakladni hodnoty - jelikoz Speed = 1 dany mensi data)\n"
printf "./$seme -f data/config -v $data\n"
./$seme -f data/config -v $data
printf "Test 1 ukoncen\n"

data='data/test1/sin_day_int.data'
printf "\nTest 2\n([Error]: Chybny prepinac)\n"
printf "./$seme -f data/config -v -x $data\n"
./$seme -f data/config -v -x $data
printf "Test 2 ukoncen\n"

printf "\nTest 3\n([Error]: Spatny configuracni soubor)\n"
printf "./$seme -f data/conf -v $data\n"
./$seme -f data/conf -v $data
printf "Test 3 ukoncen\n"

printf "\nTest 4\n([Error]: Vsechny parametry Time, FPS, Speed)\n"
printf "./$seme -f data/config -T 5 -F 25 -S 10 $data\n"
./$seme -f data/config -T 5 -F 25 -S 10 $data
printf "Test 4 dokoncen\n"

printf "\nTest 5\n([Error]: Spatne parametr Speed)\n"
printf "./$seme -f data/config -S a $data\n"
./$seme -f data/config -S a $data
printf "Test 5 dokoncen\n"

read -p "Enter..."

printf "\nTest 6\n([Error]: Spatne parametr FPS)\n"
printf "./$seme -f data/config -F b $data\n"
./$seme -f data/config -F b $data
printf "Test 6 dokoncen\n"

printf "\nTest 7\n([Error]: Spatne parametr Ymin)\n"
printf "./$seme -f data/config -y XXX $data\n"
./$seme -f data/config -y XXX $data
printf "Test 7 dokoncen\n"

printf "\nTest 8\n([Error]: Spatne parametr Ymax)\n"
printf "./$seme -f data/config -Y XXX $data\n"
./$seme -f data/config -Y XXX $data
printf "Test 8 dokoncen\n"

printf "\nTest 9\n([Error]: Spatne parametr TimeFormat)\n"
echo "./$seme -f data/config -t \"%H:%M:%S\" $data\n"
./$seme -f data/config -t '%H:%M:%S' $data
printf "Test 9 dokoncen\n"

data='data/test2/prazdny'
printf "\nTest 10\n([Error]: Prazdny vstupni soubor)\n"
printf "./$seme -f data/config $data\n"
./$seme -f data/config $data
printf "Test 10 dokoncen\n"

read -p "Enter..."

data='data/test2/sin_day_int.data'
printf "\nTest 11\n([Error]: Chyba v souboru)\n"
printf "./$seme -f data/config $data\n"
./$seme -f data/config $data
printf "Test 11 dokoncen\n"

data='http://neconeco.ne/file.txt'
printf "\nTest 12\n([Error]: Spatny link)\n"
printf "./$seme -f data/config $data\n"
./$seme -f data/config $data
printf "Test 12 dokoncen\n"

data='https://users.fit.cvut.cz/~barinkl/data4'
printf "\nTest 13\n([Error]: Link access denied)\n"
printf "./$seme -f data/config $data\n"
./$seme -f data/config $data
printf "Test 13 dokoncen\n"

data='https://xkcd.com/353'
printf "\nTest 14\n([Error]: Spatna http stranka)\n"
printf "./$seme -f data/config $data\n"
./$seme -f data/config $data
printf "Test 14 dokoncen\n"

data='data/test1/sin_day_int.da'
printf "\nTest 15\n([Error]: Spatny vstupni soubor)\n"
printf "./$seme -f data/config $data\n"
./$seme -f data/config $data
printf "Test 15 dokoncen\n"

read -p "Enter..."

data='data/test1/sin_day_int.data'
printf "\nTest 16\n(Vypis upozorneni.)\n"
printf "./$seme -f data/config2 -v -S 10 $data\n"
./$seme -f data/config2 -v -S 10 $data
printf "Test 16 dokoncen\n"

data='data/test3/sin_week_real.data'
printf "\nTest 17\n(Soubor s desetinnými čísly)\n"
printf "./$seme -f data/config -v -S 2 $data\n"
./$seme -f data/config -v -S 2 $data
printf "Test 17 dokoncen\n"

dataV='http://webdev.fit.cvut.cz/~hrabevac/sin_week_int5.data'
printf "\nTest 18\n(Stazeni z webove stranky)\n"
printf "./$seme -f data/config -v -S 3 $dataV\n"
./$seme -f data/config -v -S 3 $data
printf "Test 18 dokoncen\n"

data='data/test1/sin_day_int.data'
printf "\nTest 19\n(Stahnuti jednoho souboru a druhy v pc)\n"
printf "./$seme -f data/config -v -S 5 $dataV $data\n"
./$seme -f data/config -v -S 5 $dataV $data
printf "Test 19 dokoncen\n"

printf "\nTest 20\n(Vypis informaci)\n"
printf "./$seme -f data/config -v -F 15 -T 10 $data\n"
./$seme -f data/config -v -F 15 -T 10 $data
printf "Test 20 dokoncen\n"

read -p "Enter..."

printf "\nTest 21\n(Zmena efektu grafu)\n"
printf "./$seme -f data/config -v -S 6 -e color=blue -e method=top:color=black $data\n"
./$seme -f data/config -v -S 6 -e color=blue -e method=top:color=black $data
printf "Test 21 dokoncen\n"

printf "\nTest 22\n(Zmena nazvu grafu + zapnute upozorneni)\n"
printf "./$seme -f data/config -v -S 10 -l \"Nove jmeno\" $data\n"
./$seme -f data/config -v -S 10 -l "Nove jmeno" $data $data2
printf "Test 22 dokoncen\n"

printf "\nTest 23\n(Zmena nazvu souboru)\n"
printf "./$seme -f data/config -F 15 -T 10 -n Nova_animace $data\n"
./$seme -f data/config -F 15 -T 10 -n Nova_animace $data
printf "Test 23 dokoncen\n"

printf "\nTest 24\n(Dlouhe promenne I)\n"
printf "./$seme -f data/config --Verbose --FPS 15 --Time 10 $data\n"
./$seme -f data/config --Verbose --FPS 15 --Time 10 $data
printf "Test 24 dokoncen\n"

printf "\nTest 25\n(Dlouhe promenne II)\n"
printf "./$seme -f data/config --Verbose --Speed 10 --FPS 24 --Name Nova_animace $data\n"
./$seme -f data/config2 --Verbose --Speed 10 --FPS 24 --Name Nova_animace $data
printf "Test 25 dokoncen\n"

read -p "Enter..."

printf "\nTest 26\n(Dlouhe promenne III)\n"
printf "./$seme --ConfigFile data/config --Verbose --Speed 10 --FPS 24 --YMax max --YMin min --Legend \"Nove jmeno\" $data\n"
./$seme --ConfigFile data/config --Verbose --Speed 10 --FPS 24 --YMax max --YMin min --Legend "Nove jmeno" $data
printf "Test 26 dokoncen\n"

data='data/test1/sin_week_int.data'
printf "\nTest 27\n(Vytvoreni souboru s nejvetsim indexem + Dlouhe promenne I)\n"
printf "./$seme -f data/config --Verbose --FPS 15 --Time 10 $data\n"
./$seme -f data/config --Verbose --FPS 15 --Time 10 $data
printf "Test 27 dokoncen\n"

printf "\n"
read -p "Po Enteru smazu nejake soubory. Proto se kouknete na vsechny....."
printf "\nMazu soubory test_animation_4 test_animation_6 test_animation_3 pro ukazku \"vytvoreni souboru s nejvetsim indexem\"\n"
rm -rf test_animation_4 test_animation_6 test_animation_3

data='data/test1/sin_day_int.data'
printf "\nTest 28\n(Vytvoreni souboru s nejvetsim indexem + Dlouhe promenne I)\n"
printf "./$seme -f data/config --Verbose --FPS 15 --Time 10 $data\n"
./$seme -f data/config --Verbose --FPS 15 --Time 10 $data
printf "Test 28 dokoncen\n"
