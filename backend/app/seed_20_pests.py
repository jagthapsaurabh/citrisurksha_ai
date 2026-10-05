P20 = [
    ("citrus-psyllid", "Asian citrus psyllid", "Diaphorina citri", "Sap-sucking", "Vector of Citrus Greening (HLB)"),
    ("citrus-leaf-miner", "Citrus leaf miner", "Phyllocnistis citrella", "Leaf miner", "Mines young leaves"),
    ("citrus-blackfly", "Citrus blackfly", "Aleurocanthus woglumi", "Whitefly", "Honeydew, sooty mold"),
    ("citrus-whitefly", "Citrus whitefly", "Dialeurodes citri", "Whitefly", "Sap sucking, honeydew"),
    ("brown-citrus-aphid", "Brown citrus aphid", "Toxoptera citricida", "Aphid", "Virus transmission, curling"),
    ("cotton-aphid", "Cotton aphid", "Aphis gossypii", "Aphid", "Sap sucking"),
    ("citrus-mealybug", "Citrus mealybug", "Planococcus citri", "Mealybug", "Honeydew, fruit damage"),
    ("california-red-scale", "California red scale", "Aonidiella aurantii", "Scale insect", "Fruit and twig infestation"),
    ("purple-scale", "Purple scale", "Lepidosaphes beckii", "Scale insect", "Leaf and fruit damage"),
    ("green-shield-scale", "Green shield scale", "Coccus viridis", "Soft scale", "Honeydew production"),
    ("citrus-red-mite", "Citrus red mite", "Panonychus citri", "Mite", "Leaf bronzing"),
    ("oriental-spider-mite", "Oriental spider mite", "Eutetranychus orientalis", "Mite", "Leaf discoloration"),
    ("citrus-rust-mite", "Citrus rust mite", "Phyllocoptruta oleivora", "Mite", "Fruit russeting"),
    ("yellow-citrus-thrips", "Yellow citrus thrips", "Scirtothrips dorsalis", "Thrips", "Leaf and fruit scarring"),
    ("citrus-thrips", "Citrus thrips", "Scirtothrips citri", "Thrips", "Fruit scarring"),
    ("fruit-sucking-moth", "Fruit sucking moth", "Eudocima materna", "Moth", "Pierces ripening fruits"),
    ("lemon-butterfly", "Lemon butterfly", "Papilio demoleus", "Caterpillar", "Defoliation"),
    ("bark-eating-caterpillar", "Bark eating caterpillar", "Indarbela quadrinotata", "Borer", "Stem and branch damage"),
    ("citrus-trunk-borer", "Citrus trunk borer", "Anoplophora versteegi", "Beetle borer", "Trunk boring"),
    ("fruit-fly", "Fruit fly", "Bactrocera dorsalis", "Fruit fly", "Fruit infestation and rotting"),
]

MR_NAMES = {
    "citrus-psyllid":"आशियाई सिट्रस सायला", "citrus-leaf-miner":"सिट्रस लीफ मायनर", "citrus-blackfly":"सिट्रस काळी माशी", "citrus-whitefly":"सिट्रस पांढरी माशी",
    "brown-citrus-aphid":"तपकिरी सिट्रस मावा", "cotton-aphid":"कापूस मावा", "citrus-mealybug":"सिट्रस मिलीबग", "california-red-scale":"कॅलिफोर्निया रेड स्केल",
    "purple-scale":"जांभळा स्केल", "green-shield-scale":"हिरवा शिल्ड स्केल", "citrus-red-mite":"सिट्रस लाल कोळी", "oriental-spider-mite":"ओरिएंटल स्पायडर माइट",
    "citrus-rust-mite":"सिट्रस रस्ट माइट", "yellow-citrus-thrips":"पिवळे सिट्रस थ्रिप्स", "citrus-thrips":"सिट्रस थ्रिप्स", "fruit-sucking-moth":"फळ शोषक पतंग",
    "lemon-butterfly":"लिंबू फुलपाखरू", "bark-eating-caterpillar":"साल खाणारी अळी", "citrus-trunk-borer":"सिट्रस खोड पोखरणारा भुंगा", "fruit-fly":"फळमाशी",
}
HI_NAMES = {
    "citrus-psyllid":"एशियन सिट्रस साइलिड", "citrus-leaf-miner":"सिट्रस लीफ माइनर", "citrus-blackfly":"सिट्रस ब्लैकफ्लाई", "citrus-whitefly":"सिट्रस व्हाइटफ्लाई",
    "brown-citrus-aphid":"ब्राउन सिट्रस एफिड", "cotton-aphid":"कॉटन एफिड", "citrus-mealybug":"सिट्रस मिलीबग", "california-red-scale":"कैलिफोर्निया रेड स्केल",
    "purple-scale":"पर्पल स्केल", "green-shield-scale":"ग्रीन शील्ड स्केल", "citrus-red-mite":"सिट्रस रेड माइट", "oriental-spider-mite":"ओरिएंटल स्पाइडर माइट",
    "citrus-rust-mite":"सिट्रस रस्ट माइट", "yellow-citrus-thrips":"येलो सिट्रस थ्रिप्स", "citrus-thrips":"सिट्रस थ्रिप्स", "fruit-sucking-moth":"फ्रूट सकिंग मॉथ",
    "lemon-butterfly":"लेमन बटरफ्लाई", "bark-eating-caterpillar":"बार्क ईटिंग कैटरपिलर", "citrus-trunk-borer":"सिट्रस ट्रंक बोरर", "fruit-fly":"फल मक्खी",
}

def pest_record(pid, common, sci, ptype, damage):
    symptoms = f"Main damage: {damage}. Pest type: {ptype}. Scout leaves, shoots, fruits, twigs and trunk depending on pest location."
    prevention = "Use clean planting material, orchard sanitation, regular scouting, balanced nutrition, pruning for airflow, sticky/pheromone traps where applicable and conservation of natural enemies."
    cure = "Confirm pest identity, remove heavily infested parts where practical, use biological/organic options first and apply locally registered pesticide only as per agriculture expert recommendation."
    organic = "Neem/azadirachtin, horticultural oil/soap spray, sanitation, traps and predator/parasitoid conservation depending on pest."
    chemical = "Use locally registered insecticide/miticide in rotation by mode of action. Follow label dose, PPE and pre-harvest interval."
    mr_damage = f"मुख्य नुकसान: {damage}. नियमित निरीक्षण करा आणि कीड आढळल्यास तज्ञांचा सल्ला घ्या."
    hi_damage = f"मुख्य नुकसान: {damage}. नियमित निरीक्षण करें और कीट मिलने पर विशेषज्ञ सलाह लें।"
    return {
        "id": pid, "common_name": common, "scientific_name": sci, "category": ptype, "lifecycle": {"monitoring": "Scout crop weekly and record life stage when visible."},
        "symptoms": symptoms, "prevention": prevention, "cure": cure, "organic_control": organic, "chemical_control": chemical,
        "safety_note": "Scientist-approved recommendation required before pesticide use. Follow local label and safety instructions.",
        "translations": {
            "mr": {"common_name": MR_NAMES.get(pid, common), "symptoms": mr_damage, "prevention": "स्वच्छ रोपे, बाग स्वच्छता, नियमित निरीक्षण, संतुलित खत, हवा खेळती राहील अशी छाटणी आणि नैसर्गिक शत्रूंचे संरक्षण करा.", "cure": "कीड ओळख निश्चित करा, जास्त बाधित भाग काढा, प्रथम सेंद्रिय/जैविक उपाय वापरा आणि नोंदणीकृत औषध तज्ञ सल्ल्यानेच वापरा.", "organic_control": "नीम/अझाडिरॅक्टिन, बागायती तेल, साबण फवारणी, सापळे आणि नैसर्गिक शत्रूंचे संरक्षण.", "chemical_control": "स्थानिक नोंदणीकृत कीटकनाशक/माइटनाशक फेरपालट करून वापरा. लेबल, PPE आणि PHI पाळा.", "safety_note": "कीटकनाशक वापरण्यापूर्वी कृषी तज्ञांचा सल्ला घ्या."},
            "hi": {"common_name": HI_NAMES.get(pid, common), "symptoms": hi_damage, "prevention": "स्वच्छ पौधे, बाग स्वच्छता, नियमित निरीक्षण, संतुलित पोषण, हवा के लिए छंटाई और प्राकृतिक शत्रुओं का संरक्षण करें।", "cure": "कीट पहचान सुनिश्चित करें, अधिक संक्रमित भाग हटाएं, पहले जैविक/ऑर्गेनिक उपाय अपनाएं और पंजीकृत दवा विशेषज्ञ सलाह से ही उपयोग करें।", "organic_control": "नीम/अजाडिरैक्टिन, हॉर्टिकल्चर ऑयल, साबुन स्प्रे, ट्रैप और प्राकृतिक शत्रुओं का संरक्षण।", "chemical_control": "स्थानीय पंजीकृत कीटनाशक/माइटनाशक को रोटेशन में उपयोग करें। लेबल, PPE और PHI का पालन करें।", "safety_note": "कीटनाशक उपयोग से पहले कृषि विशेषज्ञ की सलाह लें।"}
        }
    }

TWENTY_PESTS = [pest_record(*row) for row in P20]
PEST_KNOWLEDGE_ITEMS = [{"source_type":"seed", "title": f"{common} ({sci})", "content": f"Pest type: {ptype}. Main damage: {damage}.", "pest_id": pid, "metadata": {"scientific_name": sci, "pest_type": ptype, "main_damage": damage}} for pid, common, sci, ptype, damage in P20]
