"""Default researcher-approved citrus pest guide.

This module stores trilingual pest knowledge supplied by researchers. It is seeded into:
1. Pest translations shown to farmers after detection.
2. AI knowledge items used during Train AI jobs.

Fields are intentionally JSON/dict based so we can add more languages/sections without schema changes.
"""

RESEARCHER_TRANSLATIONS = {
    "citrus-psyllid": {
        "en": {
            "common_name": "Citrus Psylla / Asian citrus psyllid",
            "identification": "Yellow almond-shaped eggs about 0.3 mm; greenish-orange nymphs; adults 3-4 mm, mottled brown, transparent wings, feeding at about 45 degrees to leaf surface.",
            "symptoms": "Nymphs and adults suck sap from tender shoots, young leaves and flower buds. Leaves curl and distort, shoots dry, honeydew causes sooty mould. Principal vector of Citrus Greening/HLB.",
            "active_period": "February-April spring flush and June-August monsoon flush.",
            "etl": "6-10 psyllids per 10 cm tender shoot.",
            "prevention": "Remove infested/dried twigs, maintain open pruned canopy, avoid sweet lime around orchards, use balanced irrigation and fertilizers to avoid excessive flushing.",
            "biological_management": "During flush spray HMO 2% or neem oil 1% or neem soap 5 g/L or pongamia soap 5 g/L. Release Mallada desjardinsi larvae twice during flush.",
            "chemical_control": "On infestation, use locally registered options such as Thiamethoxam 25 WG 0.3 g/L, Imidacloprid 17.8 SL 0.5 ml/L, Cyantraniliprole 10.26 OD 0.6 ml/L or Spirotetramat 15.31 OD 0.6 ml/L. Repeat after 15 days if required.",
            "cure": "Use integrated management: sanitation, biological/oil sprays at flush and registered insecticides only when ETL is crossed.",
        },
        "hi": {
            "common_name": "साइट्रस सायला",
            "identification": "अंडे बादाम आकार के पीले, लगभग 0.3 मि.मी.; निम्फ नारंगी; वयस्क 3-4 मि.मी. भूरे और पत्ते पर 45° कोण पर भोजन करते हैं।",
            "symptoms": "निम्फ और वयस्क नई पत्तियों व कोमल टहनियों का रस चूसते हैं। पत्तियाँ मुड़ती हैं, टहनियाँ सूखती हैं, हनीड्यू पर काली फफूंद आती है। यह HLB/ग्रीनिंग रोग का प्रमुख वाहक है।",
            "active_period": "फरवरी-अप्रैल और जून-अगस्त की नई वृद्धि।",
            "etl": "10 से.मी. नई टहनी पर 6-10 सायला।",
            "prevention": "प्रभावित टहनियाँ हटाएँ, खुली छत्र छंटाई रखें, बगीचे के आसपास मीठे नींबू से बचें, संतुलित सिंचाई व उर्वरक दें।",
            "biological_management": "नई वृद्धि पर HMO 2%, नीम तेल 1%, नीम/करंज साबुन 5 ग्राम/लीटर; Mallada desjardinsi लार्वा छोड़ें।",
            "chemical_control": "प्रकोप पर स्थानीय पंजीकृत थायमेथोक्साम, इमिडाक्लोप्रिड, सायन्ट्रानिलीप्रोल या स्पिरोटेट्रामेट लेबल अनुसार उपयोग करें।",
            "cure": "स्वच्छता, जैविक/तेल स्प्रे और ETL पार होने पर ही पंजीकृत कीटनाशक अपनाएँ।",
        },
        "mr": {
            "common_name": "सिट्रस सायला / लिंबू सायला",
            "identification": "अंडी पिवळी बदामाकार 0.3 मि.मी.; पिल्ले हिरवट-नारंगी; प्रौढ 3-4 मि.मी. तपकिरी व पानावर 45° कोनात रस शोषतात.",
            "symptoms": "पिल्ले व प्रौढ कोवळे शेंडे, पाने व कळ्यांमधील रस शोषतात. पाने मुरडतात, शेंडे वाळतात, मधासारख्या स्त्रावावर काळी बुरशी वाढते. HLB/ग्रीनिंग रोगाचा प्रमुख वाहक.",
            "active_period": "फेब्रुवारी-एप्रिल व जून-ऑगस्ट नवती काळ.",
            "etl": "10 से.मी. शेंड्यावर 6-10 सायला.",
            "prevention": "किडग्रस्त फांद्या काढा, झाडाचा घेर खुला ठेवा, गोड लिंबू झाडे आजूबाजूला टाळा, खत-पाणी संतुलित ठेवा.",
            "biological_management": "नवतीत HMO 2%, नीम तेल 1%, नीम/करंज साबण 5 ग्रॅम/लीटर; Mallada desjardinsi अळ्या सोडा.",
            "chemical_control": "प्रादुर्भाव दिसताच स्थानिक नोंदणीकृत थायमेथोक्झाम, इमिडाक्लोप्रिड, सायन्ट्रानिलीप्रोल किंवा स्पिरोटेट्रामेट लेबलप्रमाणे वापरा.",
            "cure": "स्वच्छता, जैविक/तेल फवारणी आणि ETL ओलांडल्यास नोंदणीकृत कीटकनाशक वापरा.",
        },
    },
    "citrus-blackfly": {
        "en": {"common_name": "Citrus Blackfly", "identification": "Eggs in spiral/circular patterns on underside of new leaves; later nymphs glossy black and sessile; pupae black with raised dorsal ridge.", "symptoms": "Adults and nymphs suck sap and excrete honeydew causing black sooty mould, reduced photosynthesis, weak trees, poor fruit set and quality.", "active_period": "New vegetative flush periods.", "etl": "5-10 nymphs per leaf.", "prevention": "Avoid dense planting, prevent water stagnation, avoid guava/sapota/pomegranate adjacent to citrus where possible.", "biological_management": "Neem oil 10 ml/L or neem/karanja soap 5 g/L; release Mallada desjardinsi larvae twice during flushing.", "chemical_control": "Use registered imidacloprid/chlorpyrifos-type recommendations at adult emergence or 50% egg hatch under expert guidance.", "cure": "Manage early nymphs, reduce honeydew and treat sooty mould with starch wash followed by COC where recommended."},
        "hi": {"common_name": "साइट्रस काली मक्खी", "identification": "अंडे पत्तियों की निचली सतह पर गोल/सर्पिल समूह में; बाद के निम्फ चमकीले काले और स्थिर।", "symptoms": "रस चूसकर हनीड्यू छोड़ते हैं, जिससे काली कालिखी फफूंद, प्रकाश संश्लेषण में कमी और फल गुणवत्ता घटती है।", "prevention": "घनी रोपाई और जलभराव से बचें; अमरूद, चीकू, अनार पास में न लगाएँ।", "biological_management": "नीम तेल 10 मि.ली./लीटर या नीम/करंज साबुन 5 ग्राम/लीटर; Mallada लार्वा छोड़ें।", "chemical_control": "वयस्क उद्भव/50% अंडे फूटने पर पंजीकृत कीटनाशक विशेषज्ञ सलाह से।", "cure": "प्रारंभिक निम्फ अवस्था पर नियंत्रण और सूटी मोल्ड प्रबंधन करें।"},
        "mr": {"common_name": "सिट्रस काळी माशी", "identification": "अंडी पानाच्या खालच्या बाजूला वलयात; पुढील पिल्ले चमकदार काळी व स्थिर; कोश काळा.", "symptoms": "रस शोषण व मधासारखा स्त्राव; काळी बुरशी, प्रकाशसंश्लेषण कमी, झाडे कमकुवत व फळगुणवत्ता घटते.", "prevention": "दाट लागवड व पाणी साचणे टाळा; पेरू/चिकू/डाळिंब शेजारी टाळा.", "biological_management": "नीम तेल 10 मि.ली./लीटर किंवा नीम/करंज साबण 5 ग्रॅम/लीटर; Mallada अळ्या सोडा.", "chemical_control": "प्रौढ उत्पत्ती किंवा 50% अंडी उबण्याच्या अवस्थेत नोंदणीकृत कीटकनाशक तज्ञ सल्ल्याने.", "cure": "प्रारंभिक पिल्लांवर नियंत्रण व कोळशी व्यवस्थापन करा."},
    },
    "citrus-whitefly": {
        "en": {"common_name": "Citrus Whitefly", "identification": "Yellow flattened eggs, semi-transparent nymphs attached under leaves, adults 1.5 mm yellow-bodied with white waxy wings and red eyes.", "symptoms": "Sap sucking, honeydew, sooty mould, reduced photosynthesis, lower nitrogen, reduced flowering and fruit set.", "active_period": "February-April, June-August, October-December flushes.", "etl": "5-10 nymphs per leaf.", "prevention": "Avoid dense planting, waterlogging and alternate hosts adjacent to orchard.", "biological_management": "Neem oil 1% or neem/karanja soap; conserve/release lacewings.", "chemical_control": "Imidacloprid 17.8 SL 0.5 ml/L or Chlorpyrifos 20 EC 2 ml/L only as registered/local recommendation.", "cure": "Target adults/early nymphs and manage sooty mould."},
        "hi": {"common_name": "साइट्रस सफेद मक्खी", "symptoms": "रस चूसना, हनीड्यू, काली फफूंद, प्रकाश संश्लेषण व फलधारण में कमी।", "prevention": "घनी रोपाई, जलभराव और वैकल्पिक पोषक पौधे पास में न रखें।", "cure": "वयस्क/प्रारंभिक निम्फ अवस्था पर नियंत्रण करें और सूटी मोल्ड हटाएँ।"},
        "mr": {"common_name": "सिट्रस पांढरी माशी", "symptoms": "रस शोषण, मधासारखा स्त्राव, काळी बुरशी, प्रकाशसंश्लेषण व फळधारणा कमी होते.", "prevention": "दाट लागवड, पाणी साचणे व पर्यायी यजमान शेजारी टाळा.", "cure": "प्रौढ/प्रारंभिक पिल्लांवर नियंत्रण व कोळशी व्यवस्थापन करा."},
    },
    "yellow-citrus-thrips": {
        "en": {"common_name": "Thrips", "identification": "Slender fast-moving adults about 1.5 mm; nymphs white to greenish-white with red eyes.", "symptoms": "Cup-shaped leathery leaves, silvery-white streaks near midrib, circular/irregular scars around fruit stalk and fruit surface.", "active_period": "February-April, June-July, October-December.", "etl": "10 thrips per branch tapping.", "prevention": "Monitor flush and flowering; spray HMO 2% at bud emergence and early fruit development.", "chemical_control": "Cyantraniliprole 10.26 OD 0.6 ml/L where recommended/registered.", "cure": "Protect buds and young fruits with timely monitoring and recommended sprays."},
        "hi": {"common_name": "थ्रिप्स / फूलकिड़े", "symptoms": "पत्तियाँ कप जैसी, चांदी जैसी धारियाँ और फलों पर दाग।", "prevention": "नई वृद्धि व फूल अवस्था पर निगरानी, HMO 2% छिड़काव।", "cure": "कली व छोटे फल अवस्था में समय पर नियंत्रण।"},
        "mr": {"common_name": "फुलकिडे", "symptoms": "पाने कपासारखी, चंदेरी रेषा व फळांवर डाग. बाजार गुणवत्ता घटते.", "prevention": "नवती व फुलोऱ्यात निरीक्षण, HMO 2% फवारणी.", "cure": "कळी व लहान फळ अवस्थेत वेळेवर नियंत्रण."},
    },
    "brown-citrus-aphid": {
        "en": {"common_name": "Aphids", "identification": "Soft-bodied pear-shaped adults 1.5-2.0 mm, pale yellow/green/dark/black; nymphs dark reddish-brown.", "symptoms": "Leaves yellow, curl downward, distort and dry; shoots stunt; honeydew causes sooty mould; vectors Citrus tristeza virus.", "active_period": "November-February winter flush.", "etl": "10% infested shoots.", "prevention": "Conserve parasitoids and predators; avoid unnecessary insecticide applications.", "biological_management": "Neem oil 1%, pongamia oil 1% or HMO 1.25% at first appearance.", "chemical_control": "Chlorpyrifos 20 EC 2 ml/L or Imidacloprid 17.8 SL 0.4 ml/L where locally registered.", "cure": "Treat early colonies and protect natural enemies."},
        "hi": {"common_name": "माहू / एफिड", "symptoms": "पत्तियाँ पीली व मुड़ती हैं, टहनियाँ रुकती हैं, सूटी मोल्ड और ट्रिस्टेज़ा वायरस का प्रसार।", "prevention": "प्राकृतिक शत्रुओं का संरक्षण और अनावश्यक छिड़काव से बचें।", "cure": "प्रारंभिक प्रकोप पर नीम/तेल और जरूरत पर पंजीकृत कीटनाशक।"},
        "mr": {"common_name": "मावा", "symptoms": "पाने पिवळी व मुरडतात, शेंडे खुंटतात, काळी बुरशी व ट्रिस्टेजा प्रसार होऊ शकतो.", "prevention": "मित्रकिडींचे संरक्षण व अनावश्यक फवारणी टाळा.", "cure": "प्रारंभिक प्रादुर्भावावर नीम/तेल व गरज असल्यास नोंदणीकृत कीटकनाशक."},
    },
    "citrus-mealybug": {
        "en": {"common_name": "Mealybugs", "identification": "Soft oval insects covered with white wax; eggs in cottony masses; Planococcus, Maconellicoccus and Nipaecoccus species occur.", "symptoms": "Sap sucking from fruit stalks, branches and trunks; fruit drop, honeydew, sooty mould, distorted shoots and reduced vigour.", "active_period": "April-May and October-November.", "etl": "5-10% infested fruits.", "prevention": "Prune infested branches, destroy ant colonies, sticky band around trunk, orchard sanitation.", "biological_management": "Lecanicillium lecanii 1.15% @ 5 g/L; conserve Cryptolaemus, lacewings and ladybirds.", "chemical_control": "Chlorpyrifos 20 EC 2 ml/L where registered/recommended.", "cure": "Manage ants, prune infested parts and target colonies on fruit stalks/branches."},
        "hi": {"common_name": "मिलीबग", "symptoms": "रस चूसना, फल गिरना, हनीड्यू, सूटी मोल्ड, शाखाएँ कमजोर।", "prevention": "प्रभावित शाखाएँ काटें, चींटियों को नियंत्रित करें, तने पर sticky band लगाएँ।", "cure": "चींटी प्रबंधन, जैविक कवक और पंजीकृत कीटनाशक से नियंत्रण।"},
        "mr": {"common_name": "मिलीबग / पिठ्या ढेकूण", "symptoms": "रस शोषण, फळगळ, मधासारखा स्त्राव, काळी बुरशी, झाडाची वाढ कमी.", "prevention": "बाधित फांद्या छाटणे, मुंग्या नियंत्रण, बुंध्यावर चिकट पट्टा.", "cure": "मुंग्या व्यवस्थापन, जैविक बुरशी व नोंदणीकृत कीटकनाशकाने नियंत्रण."},
    },
    "citrus-leaf-miner": {
        "en": {"common_name": "Citrus Leaf Miner", "identification": "Tiny silvery-white moth; larvae translucent inside leaves; serpentine silvery mines on tender leaves.", "symptoms": "Larvae mine leaves causing curling, drying and premature fall. Damage increases canker risk and shelters mealybugs.", "active_period": "June-September and February-April flushes.", "etl": "Nursery/young: 10% infested leaves; mature: 30% infested new leaves.", "prevention": "Avoid pruning during active flush and avoid excess nitrogen.", "biological_management": "Neem oil, HMO, azadirachtin, neem/karanja soap; conserve parasitoids, ladybirds and lacewings.", "chemical_control": "Imidacloprid 17.8 SL 0.5 ml/L or cyantraniliprole where recommended/registered.", "cure": "Protect new flush and remove highly infested growth."},
        "hi": {"common_name": "पत्ती सुरंगक / लीफ माइनर", "symptoms": "पत्तियों पर चांदी जैसी सर्पाकार सुरंग, पत्तियाँ मुड़ना और सूखना।", "prevention": "नई वृद्धि के समय छंटाई और अधिक नाइट्रोजन से बचें।", "cure": "नई कोपलों की रक्षा करें, नीम/HMO और जरूरत पर पंजीकृत दवा।"},
        "mr": {"common_name": "पाने पोखरणारी अळी / लीफ मायनर", "symptoms": "पानांवर चंदेरी नागमोडी रेषा, पाने मुरडणे व वाळणे.", "prevention": "नवतीच्या काळात छाटणी व अति नत्र टाळा.", "cure": "नवतीचे संरक्षण, नीम/HMO व गरज असल्यास नोंदणीकृत औषध."},
    },
    "lemon-butterfly": {
        "en": {"common_name": "Lemon Butterfly", "identification": "Pale yellow spherical eggs; young larvae resemble bird droppings; older larvae bright green with Y-shaped osmeterium; adult black butterfly with yellow patches.", "symptoms": "Larvae feed on leaves; severe infestation causes defoliation especially in nurseries and young orchards.", "active_period": "July-August monsoon.", "etl": "10% infested plants.", "prevention": "Handpick eggs, larvae and pupae in nurseries/young orchards.", "biological_management": "Bacillus thuringiensis 2 g/L at early larval stage, repeat at 10-day interval if needed.", "chemical_control": "Quinalphos 25 EC 2 ml/L or cyantraniliprole where recommended/registered.", "cure": "Control early larval stages before defoliation becomes severe."},
        "hi": {"common_name": "लेमन बटरफ्लाई / पत्ती खाने वाली इल्ली", "symptoms": "इल्ली पत्तियाँ खाती है; छोटे पौधे पत्तीविहीन हो सकते हैं।", "prevention": "अंडे/इल्ली हाथ से नष्ट करें और नियमित निरीक्षण करें।", "cure": "प्रारंभिक इल्ली अवस्था में Bt या पंजीकृत कीटनाशक।"},
        "mr": {"common_name": "लेमन बटरफ्लाय / पाने खाणारी अळी", "symptoms": "अळी पाने खाते; लहान झाडे निश्पर्ण होऊ शकतात.", "prevention": "अंडी/अळ्या हाताने गोळा करून नष्ट करा.", "cure": "प्रारंभिक अवस्थेत Bt किंवा नोंदणीकृत कीटकनाशक."},
    },
    "bark-eating-caterpillar": {
        "en": {"common_name": "Bark-eating Caterpillar", "identification": "Larvae 50-60 mm pinkish-brown with dark head; webbing, frass and bark dust around bore holes.", "symptoms": "Larvae tunnel at branch junctions and feed bark at night; branches dry, cracks develop and trees may die if unmanaged.", "active_period": "September-March.", "etl": "10% infested trees.", "prevention": "Clean galleries, remove webbing/frass, prune dry branches and inspect trunks after monsoon.", "chemical_control": "Inject 1% Chlorpyrifos 20 EC solution 5-10 ml per bore hole and plug opening, only as recommended.", "cure": "Mechanical killing with iron wire plus tunnel treatment and sealing."},
        "hi": {"common_name": "छाल खाने वाली इल्ली", "symptoms": "तने/शाखा में सुरंग, जाला, फ्रास; शाखाएँ सूखती हैं।", "prevention": "सुरंग साफ करें, सूखी शाखाएँ हटाएँ, नियमित निरीक्षण।", "cure": "लोहे की तार से इल्ली नष्ट करें और अनुशंसित उपचार छेद में दें।"},
        "mr": {"common_name": "खोडाची साल खाणारी अळी", "symptoms": "खोड/फांद्यांवर छिद्रे, जाळे व भुगा; फांद्या वाळतात.", "prevention": "छिद्रे साफ करणे, वाळलेल्या फांद्या काढणे, निरीक्षण.", "cure": "लोखंडी ताराने अळी नष्ट करणे व छिद्रात शिफारस केलेला उपचार."},
    },
    "fruit-sucking-moth": {
        "en": {"common_name": "Fruit-sucking Moth", "identification": "Large moth, forewings dark grey, hindwings bright orange with curved black spots; strong proboscis pierces fruit.", "symptoms": "Nocturnal adults pierce ripening fruits and suck juice; punctures allow rot, fruit drop and foul odour.", "active_period": "August-November at fruit ripening.", "etl": "10% dropped fruits due to infestation.", "prevention": "Destroy fallen fruits, remove alternate host vines, smoke with moist grass/neem branches in evening, trap crops/bagging where feasible.", "biological_management": "Neem oil 1% or HMO 2% every 10-15 days from fruit maturation to harvest.", "chemical_control": "Poison bait: Spinosad + jaggery + orange juice + water in bottles/traps where recommended.", "cure": "Use sanitation, repellence and poison bait; sprays alone are not enough."},
        "hi": {"common_name": "फल रस चूसने वाला पतंगा", "symptoms": "पतंगा पके फलों में छेद कर रस चूसता है; फल सड़ते और गिरते हैं।", "prevention": "गिरे फल नष्ट करें, वैकल्पिक लताएँ हटाएँ, धुआँ/बैगिंग/ट्रैप अपनाएँ।", "cure": "नीम/HMO और स्पिनोसैड-जग्गरी bait का उपयोग सलाह अनुसार।"},
        "mr": {"common_name": "फळातील रस शोषणारे पतंग", "symptoms": "पतंग पिकलेल्या फळांना छिद्र करून रस शोषतो; फळे सडतात व गळतात.", "prevention": "गळलेली फळे नष्ट करा, पर्यायी वेल काढा, धूर/बॅगिंग/सापळे वापरा.", "cure": "नीम/HMO आणि स्पिनोसॅड-गूळ bait सल्ल्यानुसार."},
    },
    "fruit-fly": {
        "en": {"common_name": "Fruit Fly", "identification": "Females lay eggs under semi-ripe fruit skin; larvae are creamy-white legless maggots; adults about 8 mm with yellow/dark markings.", "symptoms": "Maggots feed inside fruit causing internal rot, puncture lesions, yellowing and premature fruit drop.", "active_period": "September-November at fruit ripening.", "etl": "10% infested or prematurely dropped fruits.", "prevention": "Collect and destroy fallen/infested fruits daily, bury 50 cm deep or seal in bags, maintain sanitation, harvest on time.", "biological_management": "Orchard sanitation and parasitoid conservation; do not feed fallen fruits to livestock.", "chemical_control": "Methyl eugenol traps 20/ha; bait spray with jaggery/protein hydrolysate/yeast + spinosad; use registered insecticide only above ETL.", "cure": "Combine traps, sanitation and bait sprays because maggots inside fruit are protected from direct sprays."},
        "hi": {"common_name": "फल मक्खी", "symptoms": "मैगट फल के अंदर खाते हैं, फल सड़ते और जल्दी गिरते हैं।", "prevention": "गिरे/संक्रमित फल रोज नष्ट करें, 50 से.मी. गहरा दबाएँ, बाग स्वच्छ रखें।", "cure": "मिथाइल यूजेनॉल ट्रैप, स्वच्छता और bait spray का संयुक्त उपयोग करें।"},
        "mr": {"common_name": "फळमाशी", "symptoms": "अळ्या फळाच्या आत गर खातात; फळ सडते व अकाली गळते.", "prevention": "गळलेली/अळीग्रस्त फळे रोज नष्ट करा, 50 सें.मी. खोल पुरा, बाग स्वच्छ ठेवा.", "cure": "मिथाइल यूजेनॉल सापळे, स्वच्छता व bait spray एकत्र वापरा."},
    },
    "citrus-rust-mite": {
        "en": {"common_name": "Citrus Mites", "identification": "Rust mites are wedge-shaped and microscopic; brown mites oval and larger; green mites create fine webbing.", "symptoms": "Rust/bronzing on fruits, grey spots on leaves/fruits, chlorotic spots, dusty leaf surface, hard rough fruits and reduced market value.", "active_period": "April-May and October-December; rust mite severe August-October from fruit set to harvest.", "etl": "2% infested fruits or 10% infested leaves.", "prevention": "Avoid water stress, reduce dust, maintain balanced nutrition and conserve predators.", "biological_management": "Azadirachtin 1% 2 ml/L or neem oil 10 ml/L; HMO 2% twice at 15-day interval.", "chemical_control": "Diafenthiuron 50 WP 2 g/L or Spirotetramat 15.31 OD 6 ml/L where recommended; rotate acaricides.", "cure": "Treat early at fruit setting and repeat if required; avoid repeated pyrethroids."},
        "hi": {"common_name": "माइट / घुन", "symptoms": "फलों पर ब्रॉन्जिंग/लाल्या, पत्तियों पर धूल जैसे धब्बे, फल कठोर व खराब गुणवत्ता।", "prevention": "जल तनाव और धूल से बचें, संतुलित पोषण रखें।", "cure": "नीम/HMO और जरूरत पर पंजीकृत acaricide रोटेशन में।"},
        "mr": {"common_name": "माईट / कोळी", "symptoms": "फळांवर लाल्या/ब्रॉन्झिंग, पानांवर धुळीसारखे डाग, फळ कठीण व गुणवत्ता कमी.", "prevention": "पाण्याचा ताण व धूळ टाळा, संतुलित पोषण ठेवा.", "cure": "नीम/HMO व गरज असल्यास नोंदणीकृत acaricide फेरपालटाने."},
    },
}

# Map similar 20-class IDs to the detailed group records above.
RESEARCHER_TRANSLATIONS["cotton-aphid"] = RESEARCHER_TRANSLATIONS["brown-citrus-aphid"]
RESEARCHER_TRANSLATIONS["citrus-thrips"] = RESEARCHER_TRANSLATIONS["yellow-citrus-thrips"]
RESEARCHER_TRANSLATIONS["citrus-red-mite"] = RESEARCHER_TRANSLATIONS["citrus-rust-mite"]
RESEARCHER_TRANSLATIONS["oriental-spider-mite"] = RESEARCHER_TRANSLATIONS["citrus-rust-mite"]


def knowledge_content(pest_id: str, data: dict) -> str:
    en = data.get("en", {})
    return "\n".join([
        f"Researcher guide for {en.get('common_name', pest_id)}",
        f"Identification: {en.get('identification', '')}",
        f"Symptoms: {en.get('symptoms', '')}",
        f"Active period: {en.get('active_period', '')}",
        f"ETL: {en.get('etl', '')}",
        f"Prevention: {en.get('prevention', '')}",
        f"Biological management: {en.get('biological_management', '')}",
        f"Chemical management: {en.get('chemical_control', '')}",
        f"Cure/IPM: {en.get('cure', '')}",
    ])

RESEARCHER_GUIDE_ITEMS = [
    {"source_type": "researcher", "title": f"Researcher guide: {v.get('en', {}).get('common_name', k)}", "content": knowledge_content(k, v), "pest_id": k, "metadata": {"translations": v}}
    for k, v in RESEARCHER_TRANSLATIONS.items()
]
