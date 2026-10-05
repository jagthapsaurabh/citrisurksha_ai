import React, { createContext, useContext, useState } from 'react';

export type Lang = 'en' | 'mr' | 'hi';

const dictionaries: Record<Lang, Record<string, string>> = {
  en: {
    home: 'Home', scan: 'Scan', pestManagement: 'Pest Management', profile: 'Profile', dashboard: 'Dashboard',
    welcome: 'Welcome Farmer', welcomeText: 'Scan citrus plants, track pest history and follow expert management advice.',
    scanPest: 'Scan Pest', cameraOrGallery: 'Camera or gallery', history: 'History', fullReports: 'Full AI reports', pestGuide: 'Pest Guide', preventCure: 'Prevent & cure', yearCalendar: 'Year Calendar', calendarOperation: 'Calendar of Operation', monthCare: 'Month wise care', blog: 'Blog', advisory: 'Admin advisory', events: 'Events', alertsPrograms: 'Alerts & programs', chat: 'Chat', askSupport: 'Ask support', aboutApp: 'About App', terms: 'Terms',
    scanCitrusPest: 'Scan Citrus Pest', scanHelp: 'Take a clear close-up photo of the pest, leaf damage or fruit symptom.', clickPhoto: 'Click Photo', upload: 'Upload', aiChecking: 'AI is checking image...', confidence: 'Confidence', severity: 'Severity', stage: 'Stage', symptoms: 'Symptoms', prevention: 'Prevention', cureControl: 'Cure / Control', management: 'Management', preventive: 'Preventive', curative: 'Curative', organic: 'Organic', chemical: 'Chemical', viewFull: 'View Full Saved Result', noPest: 'No citrus pest detected. Please upload a clear citrus pest, insect or plant-damage image.',
    detectionHistory: 'Detection History', historyHelp: 'Tap any result to see full details, prevention and cure.', fullResult: 'Full Detection Result', pestDetails: 'Pest Details', lifecycle: 'Lifecycle', organicControl: 'Organic Control', chemicalControl: 'Chemical Control', aiTopResults: 'AI Top Results', correct: 'Correct', wrong: 'Wrong',
    profileTitle: 'Profile', completeProfile: 'Complete your profile', profileComplete: 'Profile Complete', farmDetails: 'Farm & Farmer Details', language: 'Language', updateProfile: 'Update Profile', more: 'More', logout: 'Logout',
    english: 'English', marathi: 'Marathi', hindi: 'Hindi', eventsAlerts: 'Events & Alerts', eventsHelp: 'Events are created by admin and notifications are sent to farmers.', farmerChat: 'Farmer Chat', chatHelp: 'Ask chatbot/support. If not satisfied, your query reaches admin panel.', send: 'Send', writeMessage: 'Write message',
  },
  mr: {
    home: 'मुख्यपृष्ठ', scan: 'स्कॅन', pestManagement: 'कीड व्यवस्थापन', profile: 'प्रोफाइल', dashboard: 'डॅशबोर्ड',
    welcome: 'शेतकरी मित्रा स्वागत आहे', welcomeText: 'लिंबूवर्गीय झाडे स्कॅन करा, कीड इतिहास पहा आणि तज्ञांचा सल्ला घ्या.',
    scanPest: 'कीड स्कॅन करा', cameraOrGallery: 'कॅमेरा किंवा गॅलरी', history: 'इतिहास', fullReports: 'पूर्ण AI अहवाल', pestGuide: 'कीड मार्गदर्शक', preventCure: 'प्रतिबंध व उपचार', yearCalendar: 'वार्षिक कॅलेंडर', calendarOperation: 'कामकाज कॅलेंडर', monthCare: 'महिन्यानुसार काळजी', blog: 'ब्लॉग', advisory: 'प्रशासक सल्ला', events: 'कार्यक्रम', alertsPrograms: 'सूचना व कार्यक्रम', chat: 'चॅट', askSupport: 'मदत विचारा', aboutApp: 'अ‍ॅप बद्दल', terms: 'अटी',
    scanCitrusPest: 'लिंबूवर्गीय कीड स्कॅन करा', scanHelp: 'कीड, पानावरील नुकसान किंवा फळावरील लक्षणाचा स्पष्ट जवळचा फोटो घ्या.', clickPhoto: 'फोटो काढा', upload: 'अपलोड', aiChecking: 'AI प्रतिमा तपासत आहे...', confidence: 'विश्वास', severity: 'तीव्रता', stage: 'अवस्था', symptoms: 'लक्षणे', prevention: 'प्रतिबंध', cureControl: 'उपचार / नियंत्रण', management: 'व्यवस्थापन', preventive: 'प्रतिबंधक', curative: 'उपचारात्मक', organic: 'सेंद्रिय', chemical: 'रासायनिक', viewFull: 'पूर्ण जतन केलेला निकाल पहा', noPest: 'लिंबूवर्गीय कीड आढळली नाही. कृपया स्पष्ट कीड, कीटक किंवा झाडाचे नुकसान असलेली प्रतिमा अपलोड करा.',
    detectionHistory: 'ओळख इतिहास', historyHelp: 'पूर्ण तपशील, प्रतिबंध आणि उपचार पाहण्यासाठी कोणत्याही निकालावर टॅप करा.', fullResult: 'पूर्ण ओळख निकाल', pestDetails: 'कीड तपशील', lifecycle: 'जीवनचक्र', organicControl: 'सेंद्रिय नियंत्रण', chemicalControl: 'रासायनिक नियंत्रण', aiTopResults: 'AI चे प्रमुख निकाल', correct: 'बरोबर', wrong: 'चुकीचे',
    profileTitle: 'प्रोफाइल', completeProfile: 'प्रोफाइल पूर्ण करा', profileComplete: 'प्रोफाइल पूर्ण', farmDetails: 'शेतकरी व शेती तपशील', language: 'भाषा', updateProfile: 'प्रोफाइल अपडेट करा', more: 'अधिक', logout: 'लॉगआउट',
    english: 'इंग्रजी', marathi: 'मराठी', hindi: 'हिंदी', eventsAlerts: 'कार्यक्रम व सूचना', eventsHelp: 'कार्यक्रम प्रशासक तयार करतात आणि शेतकऱ्यांना सूचना पाठवल्या जातात.', farmerChat: 'शेतकरी चॅट', chatHelp: 'चॅटबॉट/मदत विचारा. समाधान न झाल्यास प्रश्न प्रशासकाकडे जातो.', send: 'पाठवा', writeMessage: 'संदेश लिहा',
  },
  hi: {
    home: 'होम', scan: 'स्कैन', pestManagement: 'कीट प्रबंधन', profile: 'प्रोफाइल', dashboard: 'डैशबोर्ड',
    welcome: 'किसान मित्र आपका स्वागत है', welcomeText: 'सिट्रस पौधों को स्कैन करें, कीट इतिहास देखें और विशेषज्ञ सलाह पाएं।',
    scanPest: 'कीट स्कैन करें', cameraOrGallery: 'कैमरा या गैलरी', history: 'इतिहास', fullReports: 'पूरा AI रिपोर्ट', pestGuide: 'कीट गाइड', preventCure: 'रोकथाम व उपचार', yearCalendar: 'वार्षिक कैलेंडर', calendarOperation: 'ऑपरेशन कैलेंडर', monthCare: 'महीने अनुसार देखभाल', blog: 'ब्लॉग', advisory: 'एडमिन सलाह', events: 'कार्यक्रम', alertsPrograms: 'अलर्ट व कार्यक्रम', chat: 'चैट', askSupport: 'सहायता पूछें', aboutApp: 'ऐप के बारे में', terms: 'नियम',
    scanCitrusPest: 'सिट्रस कीट स्कैन करें', scanHelp: 'कीट, पत्ती नुकसान या फल लक्षण की स्पष्ट नज़दीकी फोटो लें।', clickPhoto: 'फोटो लें', upload: 'अपलोड', aiChecking: 'AI छवि जांच रहा है...', confidence: 'विश्वास', severity: 'गंभीरता', stage: 'अवस्था', symptoms: 'लक्षण', prevention: 'रोकथाम', cureControl: 'उपचार / नियंत्रण', management: 'प्रबंधन', preventive: 'रोकथाम', curative: 'उपचारात्मक', organic: 'जैविक', chemical: 'रासायनिक', viewFull: 'पूरा सेव किया परिणाम देखें', noPest: 'सिट्रस कीट नहीं मिला। कृपया स्पष्ट सिट्रस कीट, कीड़ा या पौधे के नुकसान वाली छवि अपलोड करें।',
    detectionHistory: 'पहचान इतिहास', historyHelp: 'पूरा विवरण, रोकथाम और उपचार देखने के लिए किसी परिणाम पर टैप करें।', fullResult: 'पूरा पहचान परिणाम', pestDetails: 'कीट विवरण', lifecycle: 'जीवनचक्र', organicControl: 'जैविक नियंत्रण', chemicalControl: 'रासायनिक नियंत्रण', aiTopResults: 'AI शीर्ष परिणाम', correct: 'सही', wrong: 'गलत',
    profileTitle: 'प्रोफाइल', completeProfile: 'प्रोफाइल पूरा करें', profileComplete: 'प्रोफाइल पूरा', farmDetails: 'किसान और खेत विवरण', language: 'भाषा', updateProfile: 'प्रोफाइल अपडेट करें', more: 'अधिक', logout: 'लॉगआउट',
    english: 'अंग्रेज़ी', marathi: 'मराठी', hindi: 'हिंदी', eventsAlerts: 'कार्यक्रम व अलर्ट', eventsHelp: 'कार्यक्रम एडमिन बनाते हैं और किसानों को नोटिफिकेशन भेजे जाते हैं।', farmerChat: 'किसान चैट', chatHelp: 'चैटबॉट/सहायता पूछें। संतुष्ट न होने पर प्रश्न एडमिन पैनल में जाएगा।', send: 'भेजें', writeMessage: 'संदेश लिखें',
  },
};

const pestTranslations: Record<string, Record<Lang, Partial<Record<'name'|'symptoms'|'prevention'|'cure'|'organic_control'|'chemical_control'|'safety_note', string>>>> = {
  'citrus-psyllid': {
    mr: { name: 'आशियाई सिट्रस सायला', symptoms: 'कोवळ्या पानांचे वाकणे, मधासारखा चिकट स्त्राव, काळी बुरशी आणि सिट्रस ग्रीनिंगचा धोका.', prevention: 'रोगमुक्त रोपे वापरा, कोवळ्या फुटीची नियमित तपासणी करा, पिवळे चिकट सापळे वापरा.', cure: 'HLB बाधित झाडावर थेट उपचार नाही; सायला नियंत्रण आणि तज्ञ सल्ल्याने बाधित झाड काढणे आवश्यक.', organic_control: 'नीम तेल, बागायती तेल, लेडीबर्ड व लेसविंगसारखे नैसर्गिक शत्रू जपणे.', chemical_control: 'स्थानिक शिफारशीनुसार नोंदणीकृत कीटकनाशक फेरपालट करून वापरा.', safety_note: 'कीटकनाशक वापरण्यापूर्वी स्थानिक कृषी विभागाचा सल्ला घ्या.' },
    hi: { name: 'एशियन सिट्रस साइलिड', symptoms: 'नई पत्तियों का मुड़ना, चिपचिपा रस, काली फफूंद और सिट्रस ग्रीनिंग का खतरा।', prevention: 'रोगमुक्त पौधे लगाएं, नई बढ़वार की नियमित जांच करें, पीले चिपचिपे ट्रैप लगाएं।', cure: 'HLB संक्रमित पेड़ का सीधा इलाज नहीं; साइलिड नियंत्रण और विशेषज्ञ सलाह जरूरी है।', organic_control: 'नीम तेल, हॉर्टिकल्चर ऑयल, लेडीबर्ड और लेसविंग जैसे मित्र कीट बचाएं।', chemical_control: 'स्थानीय सलाह के अनुसार पंजीकृत कीटनाशक रोटेशन में उपयोग करें।', safety_note: 'कीटनाशक उपयोग से पहले स्थानीय कृषि विभाग की सलाह लें।' },
    en: {},
  },
  'citrus-leaf-miner': {
    mr: { name: 'सिट्रस लीफ मायनर', symptoms: 'पानांवर चांदीसारखे वळणदार बोगदे, पानांचे वाकणे आणि रोपांची वाढ कमी होणे.', prevention: 'अति नत्र खत टाळा, अनावश्यक छाटणी टाळा, रोपवाटिकेतील रोपे तपासा.', cure: 'जास्त प्रादुर्भाव असलेल्या कोवळ्या फुटीचे संरक्षण करा व नुकसान झालेल्या फुटी काढा.', organic_control: 'नीम तेल, परजीवी कीटकांचे संरक्षण आणि फेरोमोन सापळे.', chemical_control: 'स्थानिक सल्ल्यानुसार स्पिनोसॅड/अबामेक्टिन किंवा नोंदणीकृत पर्याय वापरा.' },
    hi: { name: 'सिट्रस लीफ माइनर', symptoms: 'पत्तियों पर चांदी जैसे घुमावदार सुरंग, पत्ते मुड़ना और पौधे की वृद्धि कम होना।', prevention: 'अधिक नाइट्रोजन से बचें, अनावश्यक छंटाई न करें, नर्सरी पौधों की जांच करें।', cure: 'अधिक प्रकोप में नई बढ़वार की सुरक्षा करें और क्षतिग्रस्त भाग हटाएं।', organic_control: 'नीम तेल, परजीवी कीट संरक्षण और फेरोमोन ट्रैप।', chemical_control: 'स्थानीय सलाह अनुसार स्पिनोसैड/अबामेक्टिन या पंजीकृत विकल्प इस्तेमाल करें।' },
    en: {},
  },
};

type Ctx = { lang: Lang; setLang: (l: Lang) => void; t: (k: string) => string; pestField: (pest: any, field: string, fallback?: string) => string };
const I18nContext = createContext<Ctx>({ lang: 'en', setLang: () => undefined, t: (k) => k, pestField: (_pest, _f, fallback) => fallback ?? '' });

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>('en');
  const setLang = (l: Lang) => setLangState(l);
  const t = (k: string) => dictionaries[lang][k] ?? dictionaries.en[k] ?? k;
  const pestField = (pest: any, field: string, fallback = '') => {
    const pestId = typeof pest === 'string' ? pest : (pest?.id || pest?.pest_id);
    const apiTranslations = typeof pest === 'object' ? (pest?.translations || {}) : {};
    const localized = apiTranslations?.[lang]?.[field] ?? apiTranslations?.[lang]?.[field === 'name' ? 'common_name' : field];
    if (localized) return localized;
    if (!pestId) return fallback;
    return (pestTranslations[pestId]?.[lang] as any)?.[field] ?? (pestTranslations[pestId]?.[lang] as any)?.[field === 'name' ? 'common_name' : field] ?? fallback;
  }; 
  return <I18nContext.Provider value={{ lang, setLang, t, pestField }}>{children}</I18nContext.Provider>;
}

export function useI18n() { return useContext(I18nContext); }
