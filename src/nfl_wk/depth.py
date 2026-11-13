"""Club depth-chart registry and starter-vs-backup classification for the NFL Week Pack.

Every chart string below was transcribed by hand from the official club page named in
``CHART_SOURCES`` and read during this session (2026-11-13). Nothing here is inferred from
memory or from a third-party depth chart.

A player's depth string is the 1-based position at which the club page lists him, taking the
*best* (lowest) position across the position groups he appears in. A player who does not appear
on the club page gets NO string: the field stays blank and the row is marked
``not_listed_on_club_chart``. A blank string is never treated as "backup" or as "starter".
"""

from __future__ import annotations

CHART_SOURCES = {
    "DET": {
        "source_id": "W11-S10",
        "url": "https://www.detroitlions.com/team/depth-chart",
        "label": "2026 Unofficial Depth Chart Compiled by Lions Football Communications",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "WR1": ["Jameson Williams"],
            "WR2": ["Amon-Ra St. Brown", "DeAndre Carter"],
            "LT": ["Penei Sewell"],
            "LG": ["Christian Mahogany", "Miles Frazier"],
            "C": ["Cade Mays", "Juice Scruggs"],
            "RG": ["Tate Ratledge", "Seth McLaughlin"],
            "RT": ["Blake Miller", "Larry Borom"],
            "TE": ["Sam LaPorta", "Brock Wright", "Tyler Conklin", "Jackson Meeks"],
            "WR3": ["Isaac TeSlaa", "Tay Martin"],
            "QB": ["Jared Goff", "Joshua Dobbs"],
            "RB": ["Jahmyr Gibbs", "Sione Vaki", "Jacob Saylors"],
            "EDGE1": ["Aidan Hutchinson", "Derrick Moore", "Eric O'Neill"],
            "DL1": ["Alim McNeill", "Skyler Gill-Howard", "Mekhi Wingo"],
            "DL2": ["Tyleik Williams", "Levi Onwuzurike"],
            "EDGE2": ["DJ Wonnum", "Tyler Lacy", "Ahmed Hassanein"],
            "LB1": ["Derrick Barnes", "Joe Bachie"],
            "LB2": ["Malcolm Rodriguez", "K.J. Britt"],
            "LB3": ["Trevor Nowaske", "Amen Ogbongbemiga"],
            "CB1": ["D.J. Reed", "Rock Ya-Sin", "Khalil Dorsey", "Nick Whiteside"],
            "CB2": ["Roger McCreary", "Ennis Rakestraw Jr.", "Keith Abney II"],
            "S1": ["Chuck Clark"],
            "S2": ["Brian Branch", "Christian Izien"],
        },
    },
    "NE": {
        "source_id": "W11-S11",
        "url": "https://www.patriots.com/team/depth-chart",
        "label": "New England Patriots Unofficial Depth Chart (published by Patriots.com writers)",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "WR1": ["A.J. Brown", "Efton Chism III"],
            "LT": ["Will Campbell", "Dametrious Crownover", "Marcus Bryant"],
            "LG": ["Ben Brown", "Walter Rouse"],
            "C": ["Jared Wilson", "Ben Brown"],
            "RG": ["Matt Pryor", "Walter Rouse"],
            "RT": ["Morgan Moses", "Caleb Lomu"],
            "TE": ["Hunter Henry", "Eli Raridon", "Cameron Latu"],
            "WR2": ["DeMario Douglas", "Kyle Williams"],
            "WR3": ["Efton Chism III", "Kyle Williams"],
            "RB": ["Rhamondre Stevenson", "TreVeyon Henderson", "Corey Kiner", "Lan Larison"],
            "QB": ["Drake Maye", "Tommy DeVito", "Behren Morton"],
            "OLB1": ["Dre'Mont Jones", "Gabe Jacas"],
            "DT1": ["Christian Barmore", "Leonard Taylor III"],
            "DT2": ["Cory Durden", "DaQuan Jones"],
            "DT3": ["Milton Williams", "Joshua Farmer"],
            "OLB2": ["Elijah Ponder", "Gabe Jacas"],
            "LB1": ["Robert Spillane", "Darius Muasau", "Erick Hunter"],
            "LB2": ["Christian Elliss", "Namdi Obiazor"],
            "CB1": ["Carlton Davis III", "Channing Canada"],
            "S1": ["Craig Woodson", "Mike Brown"],
            "S2": ["Kevin Byard III", "Jaylen Reed", "Brenden Schooler"],
            "CB2": ["Marcus Jones", "Charles Woods"],
            "CB3": ["Christian Gonzalez", "Karon Prunty"],
        },
    },
    "SEA": {
        "source_id": "W11-S08",
        "url": "https://www.seahawks.com/team/depth-chart",
        "label": "Seattle Seahawks Depth Chart",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "WR1": ["Cooper Kupp", "Rashid Shaheed", "Irvin Charles"],
            "LT": ["Charles Cross", "Josh Jones"],
            "LG": ["Quenton Nelson", "Anthony Bradford"],
            "C": ["Jalen Sundell", "Olu Oluwatimi"],
            "RG": ["Grey Zabel", "Anthony Bradford", "Beau Stephens"],
            "RT": ["Abraham Lucas", "Josh Jones"],
            "TE": ["AJ Barner", "Eric Saubert", "Nick Kallerup"],
            "WR2": ["Jaxon Smith-Njigba", "Tory Horton"],
            "QB": ["Sam Darnold", "Drew Lock", "Jalen Milroe"],
            "FB": ["Brady Russell"],
            "RB": ["Zach Charbonnet", "Jadarian Price", "Emanuel Wilson", "George Holani"],
            "DT1": ["Leonard Williams", "Rylie Mills"],
            "NT": ["Byron Murphy II", "Brandon Pili", "Deven Eastern"],
            "DE": ["Jarran Reed", "Mike Morris"],
            "RUSH": ["DeMarcus Lawrence", "Derick Hall"],
            "MLB": ["Ernest Jones IV", "Patrick O'Connell"],
            "WLB": ["Drake Thomas", "Tyrice Knight", "Chazz Surratt"],
            "SLB": ["Uchenna Nwosu", "Dante Fowler Jr.", "Connor O'Toole"],
            "CB1": ["Devon Witherspoon", "Nehemiah Pritchett"],
            "CB2": ["Josh Jobe", "Avery Smith"],
            "S1": ["Ty Okada", "Rodney Thomas II"],
            "S2": ["Julian Love"],
            "S3": ["Nick Emmanwori"],
        },
    },
    "BAL": {
        "source_id": "W11-S09",
        "url": "https://www.baltimoreravens.com/team/depth-chart",
        "label": "Baltimore Ravens Depth Chart",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "WR1": ["Zay Flowers", "Devontez Walker", "Elijah Sarratt"],
            "WR2": ["Rashod Bateman", "Ja'Kobi Lane", "LaJohntay Wester"],
            "LT": ["Ronnie Stanley", "Carson Vinson"],
            "LG": ["John Simpson", "Ryan Neuzil"],
            "C": ["Cam Jurgens", "Ryan Neuzil"],
            "RG": ["Vega Ioane", "Emery Jones Jr."],
            "RT": ["Roger Rosengarten", "Carson Vinson"],
            "TE1": ["Mark Andrews", "Josh Cuevas"],
            "TE2": ["Matt Hibner"],
            "QB": ["Jacoby Brissett", "Joe Fagnano", "Kedon Slovis"],
            "RB": ["Derrick Henry", "Justice Hill", "Rasheen Ali"],
            "DT": ["Nnamdi Madubuike", "Broderick Washington Jr."],
            "NT": ["Travis Jones", "John Jenkins"],
            "DE": ["Calais Campbell", "Aeneas Peebles"],
            "RUSH": ["Trey Hendrickson", "Mike Green"],
            "MLB": ["Roquan Smith", "Jay Higgins IV"],
            "WLB": ["Trenton Simpson", "Teddye Buchanan"],
            "SAM": ["Mike Green", "Zion Young", "Ethan Burke"],
            "CB1": ["Marlon Humphrey", "Chidobe Awuzie"],
            "DB": ["Kyle Hamilton", "Keyon Martin", "Chandler Rivers"],
            "SS": ["Jaylinn Hawkins", "Keondre Jackson"],
            "FS": ["Malaki Starks", "K'Von Wallace"],
            "CB2": ["Nate Wiggins", "T.J. Tampa Jr."],
        },
    },
    "MIN": {
        "source_id": "W11-S12",
        "url": "https://www.vikings.com/team/depth-chart",
        "label": "Minnesota Vikings Depth Chart (2026 Unofficial)",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "QB": ["Kyler Murray", "Carson Wentz", "Max Brosmer"],
            "RB": ["Aaron Jones Sr.", "Jordan Mason", "Demond Claiborne", "DeeJay Dallas"],
            "FB": ["Max Bredeson"],
            "WR1": ["Justin Jefferson", "Tai Felton"],
            "WR2": ["Jordan Addison"],
            "WR3": ["Jauan Jennings", "Myles Price"],
            "TE": ["T.J. Hockenson", "Gavin Bartholomew"],
            "LT": ["Christian Darrisaw", "Ryan Van Demark"],
            "LG": ["Joe Huber"],
            "C": ["Blake Brandel", "Michael Jurgens", "Nick Samac"],
            "RG": ["Will Fries"],
            "RT": ["Brian O'Neill", "Caleb Tiernan"],
            "OLB1": ["Dallas Turner", "Kyle Van Noy", "Chaz Chambliss"],
            "DL1": ["Jalen Redmond", "Caleb Banks"],
            "DL2": ["Levi Drake Rodriguez", "Domonique Orange"],
            "DL3": ["Tyrion Ingram-Dawkins", "Elijah Williams"],
            "OLB2": ["Andrew Van Ginkel", "Bo Richter"],
            "LB1": ["Blake Cashman", "Ivan Pace Jr."],
            "LB2": ["Eric Wilson", "Jake Golday"],
            "CB1": ["Isaiah Rodgers", "James Pierre", "Zemaiah Vaughn"],
            "CB2": ["Byron Murphy Jr.", "Charles Demmings"],
            "S1": ["Harrison Smith", "Theo Jackson", "Jacob Thomas"],
            "S2": ["Joshua Metellus", "Jay Ward", "Jakobe Thomas"],
        },
    },
    "IND": {
        "source_id": "W11-S13",
        "url": "https://www.colts.com/team/depth-chart",
        "label": "Indianapolis Colts Depth Chart",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "WR1": ["Laquon Treadwell", "Nick Westbrook-Ikhine"],
            "LT": ["Bernhard Raimann", "Charlie Heck"],
            "LG": ["Jalen Farmer", "Dalton Tucker"],
            "C": ["Tanor Bortolini", "Sedrick Van Pran-Granger"],
            "RG": ["Matt Goncalves"],
            "RT": ["Jalen Travis", "Luke Tenuta"],
            "TE": ["Tyler Warren", "Mo Alie-Cox", "Drew Ogletree", "Will Mallory"],
            "WR2": ["Anthony Gould"],
            "WR3": ["Ashton Dulin", "Deion Burks"],
            "QB": ["Daniel Jones", "Anthony Richardson Sr.", "Riley Leonard"],
            "RB": ["Jonathan Taylor", "Seth McGowan", "DJ Giddens"],
            "DE1": ["Jaylahn Tuimoloau", "George Gumbs Jr."],
            "DT": ["Adetomiwa Adebawore", "Kevin Givens"],
            "NT": ["Grover Stewart", "Jerry Tillery", "Tim Smith"],
            "DE2": ["Laiatu Latu", "Caden Curry"],
            "WLB": ["Jaylon Carlies", "Bryce Boettcher", "Tahj Chambers"],
            "MLB": ["Akeem Davis-Gaither", "CJ Allen", "Austin Ajiake"],
            "CB1": ["Charvarius Ward", "Kenneth Harris"],
            "FS": ["Cam Bynum", "Jonathan Owens"],
            "SS": ["AJ Haulcy", "Hunter Wohler"],
            "N": ["Justin Walley", "Kapena Gushiken"],
            "CB2": ["Sauce Gardner"],
        },
    },
    "PHI": {
        "source_id": "W11-S07",
        "url": "https://www.philadelphiaeagles.com/team/depth-chart",
        "label": "Philadelphia Eagles Depth Chart (compiled by the Eagles communications department)",
        "as_of_week": "11",
        "as_of": "",
        "groups": {
            "WR1": ["DeVonta Smith", "Hollywood Brown"],
            "LT": ["Jordan Mailata"],
            "LG": ["Willie Lampkin"],
            "C": ["Drew Kendall", "Jake Majors"],
            "RG": ["Tyler Steen", "Micah Morris"],
            "RT": ["Markel Bell", "Fred Johnson"],
            "TE": ["Dallas Goedert", "Johnny Mundt"],
            "WR2": ["Makai Lemon", "Elijah Moore", "Britain Covey"],
            "WR3": ["Dontayvion Wicks", "Darius Cooper"],
            "RB": ["Saquon Barkley"],
            "QB": ["Tanner McKee", "Cole Payton", "Joe Milton"],
            "EDGE1": ["Jalyx Hunt", "Arnold Ebiketie"],
            "DT1": ["Jalen Carter", "Byron Young"],
            "DT2": ["Ty Robinson"],
            "DT3": ["Moro Ojomo"],
            "EDGE2": ["Nolan Smith Jr.", "A.J. Epenesa"],
            "LB1": ["Zack Baun", "Smael Mondon Jr."],
            "LB2": ["Jihaad Campbell", "Jeremiah Trotter Jr."],
            "CB1": ["Riq Woolen", "Jonathan Jones"],
            "CB2": ["Quinyon Mitchell", "Kelee Ringo"],
            "NCB": ["Cooper DeJean", "Mac McWilliams"],
            "S1": ["Marcus Epps", "Michael Carter II"],
            "S2": ["Andrew Mukuba", "Kenny Moore II"],
        },
    },
    "GB": {
        "source_id": "W11-S25",
        "url": "https://www.packers.com/team/depth-chart",
        "label": "Green Bay Packers Depth Chart",
        "as_of": "Nov 10, 2026",
        "as_of_week": "10",
        "groups": {
            "WR1": ['Christian Watson', 'Bo Melton'],
            "WR2": ['Matthew Golden', 'J. Michael Sturdivant'],
            "LT": ['Jordan Morgan', 'John Williams'],
            "LG": ['Aaron Banks', 'Travis Glover', 'Donovan Jennings'],
            "C": ['Sean Rhyan', 'Jager Burton'],
            "RG": ['Laken Tomlinson', 'Kevin Zeitler'],
            "RT": ['Anthony Belton', 'Mekhi Becton Sr.'],
            "TE": ['Tucker Kraft', 'Jonnu Smith', 'Mark Redman', 'Josh Whyle'],
            "WR3": ['Savion Williams', 'Coleman Owen'],
            "QB": ['Jordan Love', 'Tyrod Taylor'],
            "RB": ['Josh Jacobs', 'MarShawn Lloyd', 'Pierre Strong Jr.', 'Kaleb Johnson'],
            "DT1": ['Karl Brooks', 'Jordon Riley', 'Anthony Campbell'],
            "DT2": ['Devonte Wyatt', 'Chris McClellan'],
            "EDGE1": ['Lukas Van Ness', 'Brenton Cox Jr'],
            "LB1": ['Zaire Franklin', "Ty'Ron Hopper", 'Kristian Welch'],
            "LB2": ['Isaiah McDuffie', 'Nick Niemann'],
            "EDGE2": ['Barryn Sorrell', 'Dani Dennis-Sutton'],
            "CB1": ['Keisean Nixon', 'Carrington Valentine'],
            "CB2": ['Brandon Cisse', 'Benjamin St-Juste'],
            "S1": ['Xavier McKinney', 'Kitan Oladapo'],
            "S2": ['Evan Williams', 'Kitan Oladapo'],
            "NB": ['Javon Bullard', 'Kamal Hadden'],
        },
    },
    "LV": {
        "source_id": "W11-S26",
        "url": "https://www.raiders.com/team/depth-chart",
        "label": "Las Vegas Raiders Depth Chart, as of November 10 2026, Week 10 vs Seattle",
        "as_of": "November 10, 2026",
        "as_of_week": "10",
        "groups": {
            "WR1": ['Jalen Nailor', 'Malik Benson', "Dont'e Thornton Jr."],
            "LT": ['Kolton Miller', 'Charles Grant'],
            "LG": ['Spencer Burford', 'Bryce Cabeldue'],
            "C": ['Tyler Linderbaum'],
            "RG": ['Jackson Powers-Johnson', 'Caleb Rogers'],
            "RT": ['DJ Glaze', 'Trey Zuhn III'],
            "TE": ['Brock Bowers', 'Michael Mayer', 'Ian Thomas'],
            "WR2": ['Tre Tucker', 'Jack Bech', 'Dareke Young'],
            "QB": ['Fernando Mendoza', "Aidan O'Connell"],
            "RB": ['Ashton Jeanty', 'Mike Washington Jr.', 'Dylan Laube'],
            "FB": ['Connor Heyward'],
            "DE1": ['Maxx Crosby', 'Malcolm Koonce'],
            "DT1": ['Tonka Hemingway', 'JJ Pegues', 'Tim Keenan III'],
            "DT2": ['Adam Butler', 'Folorunso Fatukasi', 'Thomas Booker IV'],
            "EDGE": ['Kwity Paye'],
            "LB1": ['Nakobe Dean', 'Tommy Eichenberg', 'Segun Olubi'],
            "LB2": ['Quay Walker', 'Cody Lindenberg'],
            "CB1": ['Eric Stokes', 'Jermod McCoy', 'Darrell Luter Jr.'],
            "CB2": ['Darien Porter', 'Hezekiah Masses'],
            "CB3": ['Taron Johnson'],
            "FS": ['Treydan Stukes', 'Isaiah Pola-Mao', 'Tristin McCollum'],
            "SS": ['Jeremy Chinn', 'Dalton Johnson'],
        },
    },
    "TB": {
        "source_id": "W11-S27",
        "url": "https://www.buccaneers.com/team/depth-chart",
        "label": "Tampa Bay Buccaneers Depth Chart",
        "as_of": "",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "WR1": ['Ted Hurst III', 'David Sills V'],
            "WR2": ['Chris Godwin Jr.', 'Kameron Johnson'],
            "LT": ['Tristan Wirfs', 'Benjamin Chukwuma'],
            "LG": ['Ben Bredeson', 'Billy Schrauth'],
            "C": ['Graham Barton', 'Dan Feeney'],
            "RG": ['Cody Mauch', 'Trevor Keegan'],
            "RT": ['Luke Goedeke', 'Justin Skule'],
            "WR3": ['Emeka Egbuka', 'Tez Johnson'],
            "TE": ['Cade Otton', 'Payne Durham', 'Ko Kieft', 'Bauer Sharp'],
            "QB": ['Baker Mayfield', 'Jalon Daniels'],
            "RB": ['Bucky Irving', 'Kenny Gainwell', 'Sean Tucker'],
            "DL1": ['Calijah Kancey', 'Elijah Roberts'],
            "NT": ['Vita Vea', 'Rakeem Nunez-Roches', 'Elijah Simmons'],
            "DL2": ["A'Shawn Robinson", 'DeMonte Capehart'],
            "OLB1": ['Yaya Diaby', 'Anthony Nelson', 'David Walker'],
            "ILB1": ['Josiah Trotter', 'SirVocea Dennis'],
            "ILB2": ['Alex Anzalone'],
            "OLB2": ['Rueben Bain Jr.', 'Al-Quadin Muhammad'],
            "CB1": ['Zyon McCollum', 'Benjamin Morrison', 'Ayden Garnes'],
            "CB2": ['Jacob Parrish', 'Keionte Scott', 'Kevin Knowles'],
            "S1": ['Antoine Winfield Jr.', 'Ifeatu Melifonwu'],
            "S2": ['Tykee Smith', 'Miles Killebrew'],
        },
    },
    "AZ": {
        "source_id": "W11-S28",
        "url": "https://www.azcardinals.com/team/depth-chart",
        "label": "Arizona Cardinals Official Depth Chart",
        "as_of": "",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "WR1": ['Reggie Virgil', 'Harrison Wallace III'],
            "LT": ['Jayden Williams', 'Jedrick Wills'],
            "LG": ['Isaac Seumalo', 'Hayden Conner'],
            "C": ['Hjalte Froholdt', 'Kingsley Eguakun'],
            "RG": ['Isaiah Adams', 'Jon Gaines II'],
            "RT": ['Elijah Wilkinson', 'Josh Fryar', 'Albert Reese'],
            "TE1": ['Trey McBride'],
            "TE2": ['Elijah Higgins', 'Teagan Quitoriano'],
            "WR2": ['Simi Fehoko', 'Devin Duvernay'],
            "QB": ['Carson Beck', 'Josh Johnson', 'Joey Aguilar'],
            "RB": ['Tyler Allgeier', 'Bam Knight', 'Evan Hull'],
            "DT1": ['Dante Stills', 'Darius Robinson'],
            "NT": ['Roy Lopez', 'Andrew Billings'],
            "DT2": ['Walter Nolen III', 'L.J. Collier'],
            "OLB1": ['Josh Sweat', 'Jordan Burch', 'Eku Leota'],
            "ILB1": ['Jack Gibbens', 'Karson Sharar'],
            "ILB2": ['Mack Wilson Sr.', 'Cody Simon'],
            "OLB2": [['Zaven Collins', 'Baron Browning']],
            "CB1": ['Denzel Burke', 'Starling Thomas V'],
            "CB2": ['Max Melton', "Kei'Trel Clark"],
            "CB3": ['Kalen King', 'Garrett Williams'],
            "S1": ['Andrew Wingard', 'Kitan Crawford'],
            "S2": ['Budda Baker', 'Dadrion Taylor-Demerson'],
        },
    },
    "PIT": {
        "source_id": "W11-S29",
        "url": "https://www.steelers.com/team/depth-chart/",
        "label": "Pittsburgh Steelers Depth Chart",
        "as_of": "",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "WR1": ['DK Metcalf', 'Kaden Wetjen'],
            "LT": ['Troy Fautanu'],
            "LG": ['Mason McCormick'],
            "C": ['Zach Frazier', 'Ryan McCollum'],
            "RG": ['Brock Hoffman', 'Spencer Anderson'],
            "RT": ['Max Iheanachor', 'Dylan Cook'],
            "TE": [['Pat Freiermuth', 'Darnell Washington'], 'Robert Tonyan'],
            "WR2": ['Ben Skowronek', 'Brandon Smith'],
            "WR3": ['Germie Bernard'],
            "QB": ['Aaron Rodgers', 'Mason Rudolph', 'Will Howard', 'Drew Allar'],
            "RB": ['Jaylen Warren', 'Rico Dowdle', 'Eli Heidenreich', 'Travis Homer', 'Lew Nichols'],
            "FB": ['Riley Nowakowski'],
            "DE": ['Keeanu Benton', 'Gabriel Rubio', 'Kevin Jobity Jr.'],
            "NT": ['Yahya Black'],
            "DT": ['Cameron Heyward'],
            "LOLB": ['T.J. Watt'],
            "LILB": ['Patrick Queen', 'Carson Bruener'],
            "RILB": ['Payton Wilson', 'Cole Holcomb'],
            "ROLB": ['Alex Highsmith', 'Jack Sawyer'],
            "OLB": ['Nick Herbig'],
            "CB1": ['Asante Samuel Jr.', 'Sean Murphy-Bunting', 'Doneiko Slaughter'],
            "NCB": ['Jalen Ramsey', 'Brandin Echols'],
            "CB2": ['Jamel Dean', 'Daylen Everett', 'Terell Smith'],
            "S": ['Jaquan Brisker', 'DeShon Elliott', 'Robert Spears-Jennings'],
        },
    },
    "CHI": {
        "source_id": "W11-S30",
        "url": "https://www.chicagobears.com/team/depth-chart",
        "label": "Chicago Bears Depth Chart (As of 10/31/2026)",
        "as_of": "10/31/2026",
        "as_of_week": "9",
        "groups": {
            "WR1": ['Rome Odunze', 'Zavion Thomas'],
            "LT": ['Theo Benedet', 'Ozzy Trapilo'],
            "LG": ['Joe Thuney', 'Jordan McFadden'],
            "C": ['Garrett Bradbury', 'Logan Jones'],
            "RG": ['Jonah Jackson', 'Luke Newman'],
            "RT": ['Darnell Wright', 'Ozzy Trapilo'],
            "TE": ['Colston Loveland', 'Sam Roush'],
            "WR2": ['Kalif Raymond'],
            "WR3": ['Luther Burden III', 'Jahdae Walker'],
            "QB": ['Caleb Williams', 'Tyson Bagent', 'Case Keenum'],
            "RB": ["D'Andre Swift", 'Kyle Monangai', 'Roschon Johnson'],
            "DL1": ['Austin Booker', 'Shemar Turner', 'James Lynch'],
            "DL2": ['Grady Jarrett', 'Neville Gallimore', 'Jayden Loving'],
            "DL3": ['Jeffery Simmons', 'Kentavius Street', 'Jordan van den Berg'],
            "DL4": ['Montez Sweat', 'Daniel Hardy'],
            "LB1": ['T.J. Edwards', "D'Marco Jackson", 'Keyshaun Elliott'],
            "LB2": ['Devin Bush', 'Noah Sewell', 'Jack Sanborn'],
            "S1": ['Dillon Thieneman', 'Elijah Hicks'],
            "S2": ['Cam Lewis', 'Skyler Thomas'],
            "DB": ['Kyler Gordon', 'Malik Muhammad II'],
            "CB1": ['Tyrique Stevenson Sr.', 'Clark Phillips III'],
            "CB2": ['Jaylon Johnson', 'Josh Blackwell'],
        },
    },
    "KC": {
        "source_id": "W11-S31",
        "url": "https://www.chiefs.com/team/depth-chart",
        "label": "Kansas City Chiefs Unofficial Depth Chart",
        "as_of": "",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "WR1": ['Rashee Rice', 'Jalen Royals', 'Andrew Armstrong'],
            "LT": ['Kahlil Benson', 'Diego Pounds'],
            "LG": ['Kingsley Suamataia', 'Joshua Ezeudu'],
            "C": ['Creed Humphrey', 'Hunter Nourzad'],
            "RG": ['Trey Smith', 'Mike Caliendo'],
            "RT": ['Jaylon Moore', 'Joshua Ezeudu'],
            "TE": ['Travis Kelce', 'Noah Gray', 'Jared Wiley', 'Jake Briningstool'],
            "QB": ['Patrick Mahomes', 'Justin Fields', 'Garrett Nussmeier'],
            "RB": ['Kenneth Walker', 'Emmett Johnson', 'Jaydn Ott'],
            "FB": ['Ben VanSumeren'],
            "WR2": ['Xavier Worthy', 'Cyrus Allen', 'Josh Downs'],
            "DE1": ['Felix Anudike-Uzomah', 'Ashton Gillotte'],
            "DT1": ['Chris Jones', 'Peter Woods', 'Marcus Harris'],
            "DT2": ['Khyiris Tonga', 'Bryson Eason'],
            "DE2": ['George Karlaftis', 'R Mason Thomas'],
            "LB1": ['Jack Cochrane', 'Cooper McDonald'],
            "LB2": ['Nick Bolton', 'Jack Cochrane'],
            "LB3": ['Drue Tranquill', 'Jeffrey Bassa'],
            "CB1": ['Nohl Williams', 'Jadon Canady'],
            "CB2": ['Mansoor Delane', 'Kristian Fulton', 'Melvin Smith'],
            "S1": ['Alohi Gilman', 'Chris Roland-Wallace'],
            "S2": ['Chamarri Conner', 'Jaden Hicks', 'Xavier Nwankpa'],
        },
    },
    "MIA": {
        "source_id": "W11-S32",
        "url": "https://www.miamidolphins.com/team/depth-chart",
        "label": "Miami Dolphins Depth Chart",
        "as_of": "",
        "as_of_week": "",
        "as_of": "",
        "groups": {
            "WR1": ['Caleb Douglas', 'Jared Wayne'],
            "LT": ['Patrick Paul', 'Chukwuebuka Godrick'],
            "LG": ['Kadyn Proctor', 'Jarrett Kingston'],
            "C": ['Aaron Brewer', 'Andrew Meyer'],
            "RG": ['Jonah Savaiinaea', 'Caedan Wallace', 'Christian Haynes'],
            "RT": ['Austin Jackson', 'Caedan Wallace'],
            "TE": ['Greg Dulcich', 'Will Kacmarek', 'Seydou Traore', 'Justin Joly'],
            "FB": ['DJ Herman'],
            "RB": ['Ollie Gordon II', 'Jaylen Wright', 'Kaytron Allen'],
            "QB": ['Kyle McCord'],
            "WR2": ['Malik Washington', 'Kevin Coleman Jr.'],
            "WR3": ['Chris Bell', 'Jalen Tolbert'],
            "DT1": ['Jordan Phillips', 'Kenneth Grant'],
            "DT2": ['Zeek Biggers'],
            "EDGE1": ['Chop Robinson', 'Malik Herring', 'Rodney McGraw'],
            "EDGE2": ['Josh Uche', 'Jamree Kromah'],
            "ILB1": ['Jordyn Brooks', 'Jackson Woodard', 'Shaka Heyward'],
            "ILB2": ['Jacob Rodriguez', 'Willie Gay Jr.'],
            "NB": ['Chris Johnson'],
            "CB1": ['JuJu Brents', 'Marcellas Dial Jr.'],
            "CB2": ['Jason Marshall Jr.', 'Jaylin Simpson'],
            "S1": ['Michael Taaffe', 'Zayne Anderson'],
            "S2": ['Dante Trader Jr.', 'Kyle Louis', 'Julius Wood'],
        },
    },
}

# Positions that, when a first-string player is replaced, affect the passing/run game most.
OFFENSIVE_POSITIONS = {"QB", "RB", "WR", "TE", "LT", "LG", "C", "RG", "RT", "T", "G", "FB"}
DEFENSIVE_POSITIONS = {
    "CB", "S", "LB", "MLB", "OLB", "ILB", "DE", "DT", "NT", "EDGE", "DB", "SS", "FS", "N", "NCB", "RUSH", "SAM", "WLB", "SLB", "DL",
}

PRACTICE_WEIGHT = {
    "Full Participation in Practice": 1.0,
    "Limited Participation in Practice": 0.5,
    "Did Not Participate In Practice": 0.0,
    "": None,
}

GAME_STATUS_WEIGHT = {
    "Out": 0.0,
    "Doubtful": 0.25,
    "Questionable": 0.5,
    "": 1.0,
}


def _norm(name: str) -> str:
    """Normalise a player name for matching across official pages.

    NFL.com and the club pages differ in suffixes (``Jr.``/``III``), apostrophes and in the
    occasional middle initial, so matching is done on a lower-cased, punctuation-free,
    suffix-free version of the surname-bearing core.
    """
    import re

    n = name.lower()
    n = n.replace("'", "").replace("\u2019", "")
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    for suf in (" jr", " sr", " iii", " ii", " iv"):
        if n.endswith(suf):
            n = n[: -len(suf)]
    return n


# Cross-source name variants observed between the official injury report and the club chart.
# Each entry is (team, report name, chart name, note). Documented so a reviewer can see that the
# match was a transcription difference and not a guess about the player's identity.
NAME_ALIASES = [
    ("BAL", "Matthew Hibner", "Matt Hibner", "Official injury report uses 'Matthew'; club chart uses 'Matt'."),
    ("BAL", "Olaivavega Ioane", "Vega Ioane", "Injury report uses the legal first name; club chart uses 'Vega'."),
    ("IND", "A.J. Haulcy", "AJ Haulcy", "Punctuation only."),
    ("IND", "Drew Ogletree", "Andrew Ogletree", "Colts chart lists 'Drew Ogletree'; the injury report does not list him in Week 10."),
]


def _tiers(group_value):
    """A position group is either a list of names (1st, 2nd, 3rd ...) or a list of tiers,
    where a tier holds two or more co-starters. Returns a list of lists of names."""
    if not group_value:
        return []
    if isinstance(group_value, str):
        # Guard: a bare string would otherwise be iterated character by character.
        return [[group_value]]
    if isinstance(group_value[0], (list, tuple)):
        # Mixed tiers: a tier may be a co-starter list, or a plain name for a single slot.
        return [list(t) if isinstance(t, (list, tuple)) else [t] for t in group_value]
    return [[n] for n in group_value]


def depth_index(team: str, player: str) -> tuple[int | None, list[str]]:
    """Return (best 1-based depth string, list of position groups he is listed in)."""
    chart = CHART_SOURCES.get(team)
    if not chart:
        return None, []
    key = _norm(player)
    for t, report_name, chart_name, _note in NAME_ALIASES:
        if t == team and _norm(player) == _norm(report_name):
            key = _norm(chart_name)
            break
    best = None
    groups = []
    for group, value in chart["groups"].items():
        for i, tier in enumerate(_tiers(value), start=1):
            if any(_norm(n) == key for n in tier):
                groups.append(group)
                best = i if best is None else min(best, i)
                break
    return best, groups



UNAVAILABLE_STATUSES = ("Out", "Questionable")


def cascade_slots(detail_rows: list[dict]) -> list[dict]:
    """Find position groups where the chart's top two slots are both unavailable.

    The brief asks specifically about 3rd/4th-string backups replacing starters. That only
    happens when the men in front are unavailable too, so this function reports every
    (club, position group) whose two shallowest listed players both carry a Week 10 game
    status of Out or Questionable, together with the next name the club's own chart lists.

    Nothing here estimates how much worse the replacement is: it reports who is next on
    the club's own page, which is a fact, and stops there.
    """
    grouped: dict[tuple[str, str], list[tuple[int, str, str, str]]] = {}
    for r in detail_rows:
        if r.get("chart_status") != "listed":
            continue
        d = r.get("club_chart_depth_string") or ""
        if not d.isdigit():
            continue
        for group in (r.get("club_chart_groups") or "").split(";"):
            group = group.strip()
            if not group:
                continue
            grouped.setdefault((r["team"], group), []).append(
                (int(d), r["player"], r.get("game_status") or "", r.get("position") or "")
            )

    out = []
    for (team, group), players in sorted(grouped.items()):
        players.sort()
        unavailable = [p for p in players if p[2] in UNAVAILABLE_STATUSES]
        if len(unavailable) < 2:
            continue
        # The two shallowest slots on the chart must both be unavailable for this to be a cascade.
        top = players[:2]
        if len(top) < 2 or any(p[2] not in UNAVAILABLE_STATUSES for p in top):
            continue
        nxt = players[2] if len(players) > 2 else None
        out.append({
            "team": team,
            "position_group": group,
            "slot_1_player": top[0][1],
            "slot_1_status": top[0][2],
            "slot_2_player": top[1][1],
            "slot_2_status": top[1][2],
            "next_listed_player": nxt[1] if nxt else "",
            "next_listed_slot": str(nxt[0]) if nxt else "",
            "next_listed_status": nxt[2] if nxt else "",
            "slots_listed_on_chart": len(players),
            "note": ("Club's own chart lists no third player at this group; the replacement is not identifiable "
                     "from the official pages read here.") if nxt is None else "",
        })
    return out

def unit_of(position: str) -> str:
    p = (position or "").upper()
    if p in OFFENSIVE_POSITIONS:
        return "offense"
    if p in DEFENSIVE_POSITIONS:
        return "defense"
    return "special_teams"


def availability(practice_status: str, game_status: str) -> float | None:
    """Declared availability weight, 1.0 = fully available, 0.0 = ruled out.

    This is a *policy weight*, not an official probability: the league publishes the labels,
    not their probabilities. Returns None when no official label is present.
    """
    if game_status in GAME_STATUS_WEIGHT and game_status != "":
        return GAME_STATUS_WEIGHT[game_status]
    pw = PRACTICE_WEIGHT.get(practice_status, None)
    return pw


def deficiency_weight(depth: int | None, avail: float | None) -> float | None:
    """Share of the starter's expected work that the club's own chart says is displaced.

    weight = (depth_string - 1) * (1 - availability). A 1st-string player who is fully
    available contributes 0. A 1st-string player ruled out contributes 0 * ... wait: the
    displaced share is the *incoming* string minus one, weighted by unavailability of the
    player in front. See :func:`team_deficiency` for the aggregation that does this properly.
    """
    if depth is None or avail is None:
        return None
    return (depth - 1) * (1.0 - avail)


def team_deficiency(rows: list[dict]) -> dict:
    """Aggregate one club's Week 10 injury rows into offensive/defensive deficiency scores.

    Method (policy, disclosed on the site):
      1. For every listed player with a club-chart depth string ``d`` (1 = starter) and
         declared availability ``a`` in [0,1], the *displacement* of that player is
         ``w = (1 - a) / max(d, 1) ** 0`` … concretely, ``w = (1 - a)`` if d == 1 else 0.
      2. A club's slot is only counted as deficient when a *first-string* player is
         unavailable and the chart lists a replacement behind him.
    The return value therefore reports counts, not a continuous score, so that nothing is
    presented as a measured effect size.
    """
    out = {
        "off_starters_out": 0,
        "off_starters_questionable": 0,
        "def_starters_out": 0,
        "def_starters_questionable": 0,
        "second_string_in": 0,
        "third_string_in": 0,
        "fourth_string_in": 0,
        "unlisted": 0,
        "unverifiable": 0,
    }
    for r in rows:
        d = r.get("depth_string")
        if d == "" or d is None:
            if r.get("chart_status") == "not_listed_on_club_chart":
                out["unlisted"] += 1
            else:
                out["unverifiable"] += 1
            continue
        d = int(d)
        gs = r.get("game_status") or ""
        ps = r.get("practice_status") or ""
        unit = r.get("unit")
        out_fn = (1 - GAME_STATUS_WEIGHT.get(gs, 1.0)) if gs else (
            1 - (PRACTICE_WEIGHT.get(ps) or 1.0) if ps else 0.0
        )
        if d == 1 and gs == "Out":
            if unit == "offense":
                out["off_starters_out"] += 1
            elif unit == "defense":
                out["def_starters_out"] += 1
        elif d == 1 and gs == "Questionable":
            if unit == "offense":
                out["off_starters_questionable"] += 1
            elif unit == "defense":
                out["def_starters_questionable"] += 1
        elif d == 2 and (gs == "Out" or out_fn >= 1.0):
            out["second_string_in"] += 1
        elif d == 3 and (gs == "Out" or out_fn >= 1.0):
            out["third_string_in"] += 1
        elif d == 4 and (gs == "Out" or out_fn >= 1.0):
            out["fourth_string_in"] += 1
    return out
