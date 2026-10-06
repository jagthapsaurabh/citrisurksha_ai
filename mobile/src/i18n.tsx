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
    loginTitle: 'Farmer Login', phonePh: 'Phone number', passwordPh: 'Password', loginBtn: 'Login', registerLink: 'New farmer? Register here', loginFailed: 'Login failed', checkDetails: 'Please check phone/password',
    registerTitle: 'Create Farmer Account', fullName: 'Full name', phone: 'Phone', district: 'District', confirmPh: 'Confirm password', registerBtn: 'Register', pleaseWait: 'Please wait...', regFailed: 'Registration failed',
    nameRequired: 'Name is required', phoneRequired: 'Phone is required', passShort: 'Password must be at least 6 characters', passMismatch: 'Password and confirm password do not match',
    statusVerified: 'Verified by admin', statusCorrected: 'Corrected by admin', statusPending: 'pending', noDetections: 'No detections yet. Use Scan to detect your first pest.',
    correctedBy: 'Corrected by admin/agronomist', statusLbl: 'Status', adminNote: 'Admin note', thanks: 'Thank you', fbSaved: 'Feedback saved.', fbReview: 'Feedback saved for expert review.', fbFailed: 'Feedback failed', loadFailed: 'Could not load result',
    sevHigh: 'High', sevMedium: 'Medium', sevLow: 'Low', sevPreliminary: 'Preliminary', sevNone: 'none',
    searchPest: 'Search pest', dataNotAvailable: 'Data not available', loading: 'Loading...',
    calendarHelp: 'Month-wise calendar is managed by admin from database.', tapToView: 'Tap to view operation',
    blogHelp: 'Advisory articles are published from the admin panel.', readDetails: 'Read details', byAuthor: 'By', openDoc: 'Open Document', like: 'Like', postComment: 'Post Comment', likeFailed: 'Like failed', commentFailed: 'Comment failed', commentEmpty: 'Comment cannot be empty',
    insecticidesTitle: 'Recommended insecticides (CIB-RC)',
    notificationsTitle: 'Notifications', clearAll: 'Clear all', delete: 'Delete', seen: 'Seen', newStatus: 'New',
    startNewChat: '＋ Start New Chat', chatError: 'Chat error', attachFirst: 'Start chat first', attachErr: 'Attachment error',
    chatBotSpray: 'Please check Recommended insecticides (CIB-RC) and verify with agriculture officer before spraying.', chatBotPest: 'Upload a clear image in Scan tab. If result is not satisfactory, this chat is visible to admin support.', chatBotDefault: 'Thanks. I have noted your query. If this answer is not enough, admin/support will reply here.',
    edit: 'Edit', cancel: 'Cancel', saving: 'Saving...', saved: 'Saved', profileUpdated: 'Profile updated successfully.', couldNotSave: 'Could not save profile', profileError: 'Profile error', langUpdateFailed: 'Language update failed', notAvailable: 'Not available', logoutConfirm: 'Are you sure you want to logout?', yes: 'Yes',
    fName: 'Full Name', fEmail: 'Email', fVillage: 'Village', fDistrict: 'District', fState: 'State', fAddress: 'Address', fAcres: 'Land in acres', fPlants: 'Plants/Crops you have', fVarieties: 'Citrus varieties', fIrrigation: 'Irrigation type', fExperience: 'Farming experience years',
    aboutText1: 'CitriSurksha helps citrus farmers detect pests and insects from plant photos, view prevention and cure guidance, and maintain detection history.', aboutText2: 'The pest catalogue, blog, yearly calendar and AI review data are managed from the admin panel and backend database.', version: 'Version',
    termsTitle: 'Terms & Conditions',
    terms1: '1. CitriSurksha AI results are advisory and should be verified by an agriculture expert for severe infestations.',
    terms2: '2. Follow local agriculture department guidance, pesticide labels, PPE requirements and pre-harvest intervals.',
    terms3: '3. Uploaded images may be reviewed by authorised admins/agronomists to improve service quality.',
    terms4: '4. Farmer images are not used for AI training unless approved through the admin review workflow.',
    terms5: '5. Keep your profile and farm details accurate to receive better recommendations.',
    titleHistory: 'Detection History', titleDetection: 'Detection Result', titleBlog: 'Blog & Advisory', titleBlogDetail: 'Blog Details',
  },
  mr: {
    home: 'मुख्यपृष्ठ', scan: 'स्कॅन', pestManagement: 'कीड व्यवस्थापन', profile: 'प्रोफाइल', dashboard: 'डॅशबोर्ड',
    welcome: 'शेतकरी मित्रा स्वागत आहे', welcomeText: 'लिंबूवर्गीय झाडे स्कॅन करा, कीड इतिहास पहा आणि तज्ञांचा सल्ला घ्या.',
    scanPest: 'कीड स्कॅन करा', cameraOrGallery: 'कॅमेरा किंवा गॅलरी', history: 'इतिहास', fullReports: 'पूर्ण AI अहवाल', pestGuide: 'कीड मार्गदर्शक', preventCure: 'प्रतिबंध व उपचार', yearCalendar: 'वार्षिक कॅलेंडर', calendarOperation: 'कामकाज कॅलेंडर', monthCare: 'महिन्यानुसार काळजी', blog: 'ब्लॉग', advisory: 'प्रशासक सल्ला', events: 'कार्यक्रम', alertsPrograms: 'सूचना व कार्यक्रम', chat: 'चॅट', askSupport: 'मदत विचारा', aboutApp: 'अ‍ॅप बद्दल', terms: 'अटी',
    scanCitrusPest: 'लिंबूवर्गीय कीड स्कॅन करा', scanHelp: 'कीड, पानावरील नुकसान किंवा फळावरील लक्षणाचा स्पष्ट जवळचा फोटो घ्या.', clickPhoto: 'फोटो काढा', upload: 'अपलोड', aiChecking: 'AI प्रतिमा तपासत आहे...', confidence: 'विश्वास', severity: 'तीव्रता', stage: 'अवस्था', symptoms: 'लक्षणे', prevention: 'प्रतिबंध', cureControl: 'उपचार / नियंत्रण', management: 'व्यवस्थापन', preventive: 'प्रतिबंधक', curative: 'उपचारात्मक', organic: 'सेंद्रिय', chemical: 'रासायनिक', viewFull: 'पूर्ण जतन केलेला निकाल पहा', noPest: 'लिंबूवर्गीय कीड आढळली नाही. कृपया स्पष्ट कीड, कीटक किंवा झाडाचे नुकसान असलेली प्रतिमा अपलोड करा.',
    detectionHistory: 'ओळख इतिहास', historyHelp: 'पूर्ण तपशील, प्रतिबंध आणि उपचार पाहण्यासाठी कोणत्याही निकालावर टॅप करा.', fullResult: 'पूर्ण ओळख निकाल', pestDetails: 'कीड तपशील', lifecycle: 'जीवनचक्र', organicControl: 'सेंद्रिय नियंत्रण', chemicalControl: 'रासायनिक नियंत्रण', aiTopResults: 'AI चे प्रमुख निकाल', correct: 'बरोबर', wrong: 'चुकीचे',
    profileTitle: 'प्रोफाइल', completeProfile: 'प्रोफाइल पूर्ण करा', profileComplete: 'प्रोफाइल पूर्ण', farmDetails: 'शेतकरी व शेती तपशील', language: 'भाषा', updateProfile: 'प्रोफाइल अपडेट करा', more: 'अधिक', logout: 'लॉगआउट',
    english: 'इंग्रजी', marathi: 'मराठी', hindi: 'हिंदी', eventsAlerts: 'कार्यक्रम व सूचना', eventsHelp: 'कार्यक्रम प्रशासक तयार करतात आणि शेतकऱ्यांना सूचना पाठवल्या जातात.', farmerChat: 'शेतकरी चॅट', chatHelp: 'चॅटबॉट/मदत विचारा. समाधान न झाल्यास प्रश्न प्रशासकाकडे जातो.', send: 'पाठवा', writeMessage: 'संदेश लिहा',
    loginTitle: 'शेतकरी लॉगिन', phonePh: 'मोबाईल नंबर', passwordPh: 'पासवर्ड', loginBtn: 'लॉगिन', registerLink: 'नवीन शेतकरी? येथे नोंदणी करा', loginFailed: 'लॉगिन अयशस्वी', checkDetails: 'कृपया फोन/पासवर्ड तपासा',
    registerTitle: 'शेतकरी खाते तयार करा', fullName: 'पूर्ण नाव', phone: 'फोन', district: 'जिल्हा', confirmPh: 'पासवर्ड निश्चित करा', registerBtn: 'नोंदणी', pleaseWait: 'कृपया थांबा...', regFailed: 'नोंदणी अयशस्वी',
    nameRequired: 'नाव आवश्यक आहे', phoneRequired: 'फोन आवश्यक आहे', passShort: 'पासवर्ड किमान 6 अक्षरांचा असावा', passMismatch: 'पासवर्ड व पुष्टी पासवर्ड जुळत नाहीत',
    statusVerified: 'प्रशासकाने सत्यापित', statusCorrected: 'प्रशासकाने दुरुस्त केले', statusPending: 'प्रलंबित', noDetections: 'अजून ओळख नाही. पहिली कीड ओळखण्यासाठी स्कॅन वापरा.',
    correctedBy: 'प्रशासक/कृषीतज्ञाने दुरुस्त केले', statusLbl: 'स्थिती', adminNote: 'प्रशासक टीपा', thanks: 'धन्यवाद', fbSaved: 'अभिप्राय जतन झाला.', fbReview: 'तज्ञ आढाव्यासाठी अभिप्राय जतन.', fbFailed: 'अभिप्राय अयशस्वी', loadFailed: 'निकाल लोड होऊ शकला नाही',
    sevHigh: 'जास्त', sevMedium: 'मध्यम', sevLow: 'कमी', sevPreliminary: 'प्राथमिक', sevNone: 'काही नाही',
    searchPest: 'कीड शोधा', dataNotAvailable: 'माहिती उपलब्ध नाही', loading: 'लोड होत आहे...',
    calendarHelp: 'महिन्यानुसार कॅलेंडर प्रशासक डेटाबेसमधून व्यवस्थापित करतात.', tapToView: 'पाहण्यासाठी टॅप करा',
    blogHelp: 'सल्ला लेख प्रशासक पॅनलमधून प्रकाशित होतात.', readDetails: 'तपशील वाचा', byAuthor: 'लेखक', openDoc: 'दस्तऐवज उघडा', like: 'आवड', postComment: 'टिप्पणी पोस्ट करा', likeFailed: 'आवड अयशस्वी', commentFailed: 'टिप्पणी अयशस्वी', commentEmpty: 'टिप्पणी रिकामी असू शकत नाही',
    insecticidesTitle: 'शिफारस कीटकनाशके (CIB-RC)',
    notificationsTitle: 'सूचना', clearAll: 'सर्व साफ करा', delete: 'हटवा', seen: 'पाहिले', newStatus: 'नवीन',
    startNewChat: '＋ नवीन चॅट सुरू करा', chatError: 'चॅट त्रुटी', attachFirst: 'आधी चॅट सुरू करा', attachErr: 'जोडणी त्रुटी',
    chatBotSpray: 'कृपया शिफारस कीटकनाशके (CIB-RC) पहा आणि फवारणीपूर्वी कृषी अधिकाऱ्यांकडून खात्री करा.', chatBotPest: 'स्कॅन टॅबमध्ये स्पष्ट प्रतिमा अपलोड करा. समाधान न झाल्यास ही चॅट प्रशासक पाहतात.', chatBotDefault: 'धन्यवाद. तुमचा प्रश्न नोंदवला आहे. पुरेसे नसल्यास प्रशासक/मदत येथे उत्तर देतील.',
    edit: 'संपादन', cancel: 'रद्द करा', saving: 'जतन होत आहे...', saved: 'जतन झाले', profileUpdated: 'प्रोफाइल यशस्वीरित्या अपडेट.', couldNotSave: 'प्रोफाइल जतन होऊ शकली नाही', profileError: 'प्रोफाइल त्रुटी', langUpdateFailed: 'भाषा अपडेट अयशस्वी', notAvailable: 'उपलब्ध नाही', logoutConfirm: 'तुम्हाला लॉगआउट करायचे आहे का?', yes: 'हो',
    fName: 'पूर्ण नाव', fEmail: 'ईमेल', fVillage: 'गाव', fDistrict: 'जिल्हा', fState: 'राज्य', fAddress: 'पत्ता', fAcres: 'शेती एकरमध्ये', fPlants: 'तुमची झाडे/पिके', fVarieties: 'सिट्रस वाण', fIrrigation: 'सिंचन प्रकार', fExperience: 'शेती अनुभव वर्षे',
    aboutText1: 'सिट्रीसुरक्षा शेतकऱ्यांना झाडांच्या फोटोवरून कीड ओळखण्यास, प्रतिबंध व उपचार मार्गदर्शन पाहण्यास आणि ओळख इतिहास ठेवण्यास मदत करते.', aboutText2: 'कीड सूची, ब्लॉग, वार्षिक कॅलेंडर व AI आढावा माहिती प्रशासक पॅनल व डेटाबेसमधून व्यवस्थापित होते.', version: 'आवृत्ती',
    termsTitle: 'अटी व शर्ती',
    terms1: '1. सिट्रीसुरक्षा AI चे निकाल सल्लामूलक आहेत; गंभीर प्रादुर्भाव्यात कृषी तज्ञांचा सल्ला घ्या.',
    terms2: '2. स्थानिक कृषी विभागाचे मार्गदर्शन, कीटकनाशक लेबल, PPE व पीक कापणीपूर्व अंतर पाळा.',
    terms3: '3. सेवा सुधारण्यासाठी अधिकृत प्रशासक/कृषीतज्ञ अपलोड केलेल्या प्रतिमा तपासू शकतात.',
    terms4: '4. प्रशासक आढावा प्रक्रियेतून मंजूर होईपर्यंत शेतकऱ्यांच्या प्रतिमा AI प्रशिक्षणासाठी वापरल्या जात नाहीत.',
    terms5: '5. चांगल्या शिफारशींसाठी प्रोफाइल व शेती तपशील अचूक ठेवा.',
    titleHistory: 'ओळख इतिहास', titleDetection: 'ओळख निकाल', titleBlog: 'ब्लॉग व सल्ला', titleBlogDetail: 'ब्लॉग तपशील',
  },
  hi: {
    home: 'होम', scan: 'स्कैन', pestManagement: 'कीट प्रबंधन', profile: 'प्रोफाइल', dashboard: 'डैशबोर्ड',
    welcome: 'किसान मित्र आपका स्वागत है', welcomeText: 'सिट्रस पौधों को स्कैन करें, कीट इतिहास देखें और विशेषज्ञ सलाह पाएं।',
    scanPest: 'कीट स्कैन करें', cameraOrGallery: 'कैमरा या गैलरी', history: 'इतिहास', fullReports: 'पूरा AI रिपोर्ट', pestGuide: 'कीट गाइड', preventCure: 'रोकथाम व उपचार', yearCalendar: 'वार्षिक कैलेंडर', calendarOperation: 'ऑपरेशन कैलेंडर', monthCare: 'महीने अनुसार देखभाल', blog: 'ब्लॉग', advisory: 'एडमिन सलाह', events: 'कार्यक्रम', alertsPrograms: 'अलर्ट व कार्यक्रम', chat: 'चैट', askSupport: 'सहायता पूछें', aboutApp: 'ऐप के बारे में', terms: 'नियम',
    scanCitrusPest: 'सिट्रस कीट स्कैन करें', scanHelp: 'कीट, पत्ती नुकसान या फल लक्षण की स्पष्ट नज़दीकी फोटो लें।', clickPhoto: 'फोटो लें', upload: 'अपलोड', aiChecking: 'AI छवि जांच रहा है...', confidence: 'विश्वास', severity: 'गंभीरता', stage: 'अवस्था', symptoms: 'लक्षण', prevention: 'रोकथाम', cureControl: 'उपचार / नियंत्रण', management: 'प्रबंधन', preventive: 'रोकथाम', curative: 'उपचारात्मक', organic: 'जैविक', chemical: 'रासायनिक', viewFull: 'पूरा सेव किया परिणाम देखें', noPest: 'सिट्रस कीट नहीं मिला। कृपया स्पष्ट सिट्रस कीट, कीड़ा या पौधे के नुकसान वाली छवि अपलोड करें।',
    detectionHistory: 'पहचान इतिहास', historyHelp: 'पूरा विवरण, रोकथाम और उपचार देखने के लिए किसी परिणाम पर टैप करें।', fullResult: 'पूरा पहचान परिणाम', pestDetails: 'कीट विवरण', lifecycle: 'जीवनचक्र', organicControl: 'जैविक नियंत्रण', chemicalControl: 'रासायनिक नियंत्रण', aiTopResults: 'AI शीर्ष परिणाम', correct: 'सही', wrong: 'गलत',
    profileTitle: 'प्रोफाइल', completeProfile: 'प्रोफाइल पूरा करें', profileComplete: 'प्रोफाइल पूरा', farmDetails: 'किसान और खेत विवरण', language: 'भाषा', updateProfile: 'प्रोफाइल अपडेट करें', more: 'अधिक', logout: 'लॉगआउट',
    english: 'अंग्रेज़ी', marathi: 'मराठी', hindi: 'हिंदी', eventsAlerts: 'कार्यक्रम व अलर्ट', eventsHelp: 'कार्यक्रम एडमिन बनाते हैं और किसानों को नोटिफिकेशन भेजे जाते हैं।', farmerChat: 'किसान चैट', chatHelp: 'चैटबॉट/सहायता पूछें। संतुष्ट न होने पर प्रश्न एडमिन पैनल में जाएगा।', send: 'भेजें', writeMessage: 'संदेश लिखें',
    loginTitle: 'किसान लॉगिन', phonePh: 'मोबाइल नंबर', passwordPh: 'पासवर्ड', loginBtn: 'लॉगिन', registerLink: 'नया किसान? यहाँ पंजीकरण करें', loginFailed: 'लॉगिन विफल', checkDetails: 'कृपया फोन/पासवर्ड जाँचें',
    registerTitle: 'किसान खाता बनाएं', fullName: 'पूरा नाम', phone: 'फोन', district: 'जिला', confirmPh: 'पासवर्ड पुष्टि करें', registerBtn: 'पंजीकरण', pleaseWait: 'कृपया प्रतीक्षा करें...', regFailed: 'पंजीकरण विफल',
    nameRequired: 'नाम आवश्यक है', phoneRequired: 'फोन आवश्यक है', passShort: 'पासवर्ड कम से कम 6 अक्षरों का हो', passMismatch: 'पासवर्ड और पुष्टि पासवर्ड मेल नहीं खाते',
    statusVerified: 'एडमिन द्वारा सत्यापित', statusCorrected: 'एडमिन द्वारा सुधारा गया', statusPending: 'लंबित', noDetections: 'अभी कोई पहचान नहीं। पहला कीट पहचानने के लिए स्कैन उपयोग करें।',
    correctedBy: 'एडमिन/कृषि विशेषज्ञ द्वारा सुधारा गया', statusLbl: 'स्थिति', adminNote: 'एडमिन नोट', thanks: 'धन्यवाद', fbSaved: 'प्रतिक्रिया सहेजी गई।', fbReview: 'विशेषज्ञ समीक्षा हेतु प्रतिक्रिया सहेजी गई।', fbFailed: 'प्रतिक्रिया विफल', loadFailed: 'परिणाम लोड नहीं हो सका',
    sevHigh: 'उच्च', sevMedium: 'मध्यम', sevLow: 'निम्न', sevPreliminary: 'प्रारंभिक', sevNone: 'कोई नहीं',
    searchPest: 'कीट खोजें', dataNotAvailable: 'डेटा उपलब्ध नहीं', loading: 'लोड हो रहा है...',
    calendarHelp: 'माहवार कैलेंडर एडमिन डेटाबेस से प्रबंधित करते हैं।', tapToView: 'देखने के लिए टैप करें',
    blogHelp: 'सलाह लेख एडमिन पैनल से प्रकाशित होते हैं।', readDetails: 'विवरण पढ़ें', byAuthor: 'द्वारा', openDoc: 'दस्तावेज़ खोलें', like: 'पसंद', postComment: 'टिप्पणी पोस्ट करें', likeFailed: 'पसंद विफल', commentFailed: 'टिप्पणी विफल', commentEmpty: 'टिप्पणी खाली नहीं हो सकती',
    insecticidesTitle: 'अनुशंसित कीटनाशक (CIB-RC)',
    notificationsTitle: 'सूचनाएं', clearAll: 'सभी साफ़ करें', delete: 'हटाएं', seen: 'देखा', newStatus: 'नया',
    startNewChat: '＋ नई चैट शुरू करें', chatError: 'चैट त्रुटि', attachFirst: 'पहले चैट शुरू करें', attachErr: 'अनुलग्नक त्रुटि',
    chatBotSpray: 'कृपया अनुशंसित कीटनाशक (CIB-RC) देखें और छिड़काव से पहले कृषि अधिकारी से पुष्टि करें।', chatBotPest: 'स्कैन टैब में स्पष्ट छवि अपलोड करें। संतुष्ट न होने पर यह चैट एडमिन सहायता देखेगी।', chatBotDefault: 'धन्यवाद। आपका प्रश्न नोट कर लिया है। पर्याप्त न होने पर एडमिन/सहायता यहाँ उत्तर देंगे।',
    edit: 'संपादित करें', cancel: 'रद्द करें', saving: 'सहेजा जा रहा है...', saved: 'सहेजा गया', profileUpdated: 'प्रोफाइल सफलतापूर्वक अपडेट।', couldNotSave: 'प्रोफाइल सहेजा नहीं जा सका', profileError: 'प्रोफाइल त्रुटि', langUpdateFailed: 'भाषा अपडेट विफल', notAvailable: 'उपलब्ध नहीं', logoutConfirm: 'क्या आप लॉगआउट करना चाहते हैं?', yes: 'हाँ',
    fName: 'पूरा नाम', fEmail: 'ईमेल', fVillage: 'गाँव', fDistrict: 'जिला', fState: 'राज्य', fAddress: 'पता', fAcres: 'भूमि एकड़ में', fPlants: 'आपके पौधे/फसलें', fVarieties: 'सिट्रस किस्में', fIrrigation: 'सिंचाई प्रकार', fExperience: 'खेती अनुभव वर्ष',
    aboutText1: 'सिट्रीसुरक्षा किसानों को पौधों की फोटो से कीट पहचानने, रोकथाम व उपचार मार्गदर्शन देखने और पहचान इतिहास रखने में मदद करता है।', aboutText2: 'कीट सूची, ब्लॉग, वार्षिक कैलेंडर व AI समीक्षा डेटा एडमिन पैनल व डेटाबेस से प्रबंधित होता है।', version: 'संस्करण',
    termsTitle: 'नियम व शर्तें',
    terms1: '1. सिट्रीसुरक्षा AI परिणाम सलाहकार हैं; गंभीर प्रकोप में कृषि विशेषज्ञ से सत्यापित करें।',
    terms2: '2. स्थानीय कृषि विभाग मार्गदर्शन, कीटनाशक लेबल, PPE और पूर्व-कटाई अंतराल का पालन करें।',
    terms3: '3. सेवा गुणवत्ता सुधारने हेतु अधिकृत एडमिन/कृषि विशेषज्ञ अपलोड की गई छवियाँ देख सकते हैं।',
    terms4: '4. एडमिन समीक्षा प्रक्रिया से स्वीकृत होने तक किसान की छवियाँ AI प्रशिक्षण में उपयोग नहीं होतीं।',
    terms5: '5. बेहतर सिफारिशों के लिए प्रोफाइल और खेत विवरण सटीक रखें।',
    titleHistory: 'पहचान इतिहास', titleDetection: 'पहचान परिणाम', titleBlog: 'ब्लॉग व सलाह', titleBlogDetail: 'ब्लॉग विवरण',
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

type Ctx = { lang: Lang; locale: string; setLang: (l: Lang) => void; t: (k: string) => string; pestField: (pest: any, field: string, fallback?: string) => string; fmtDate: (iso?: string) => string };
const I18nContext = createContext<Ctx>({ lang: 'en', locale: 'en-IN', setLang: () => undefined, t: (k) => k, pestField: (_pest, _f, fallback) => fallback ?? '', fmtDate: (iso) => iso ?? '' });

const LOCALES: Record<Lang, string> = { en: 'en-IN', mr: 'mr-IN', hi: 'hi-IN' };

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>('en');
  const setLang = (l: Lang) => setLangState(l);
  const t = (k: string) => dictionaries[lang][k] ?? dictionaries.en[k] ?? k;
  const fmtDate = (iso?: string) => { try { return iso ? new Date(iso).toLocaleString(LOCALES[lang]) : ''; } catch { return iso ?? ''; } };
  const pestField = (pest: any, field: string, fallback = '') => {
    const pestId = typeof pest === 'string' ? pest : (pest?.id || pest?.pest_id);
    const apiTranslations = typeof pest === 'object' ? (pest?.translations || {}) : {};
    const localized = apiTranslations?.[lang]?.[field] ?? apiTranslations?.[lang]?.[field === 'name' ? 'common_name' : field];
    if (localized) return localized;
    if (!pestId) return fallback;
    return (pestTranslations[pestId]?.[lang] as any)?.[field] ?? (pestTranslations[pestId]?.[lang] as any)?.[field === 'name' ? 'common_name' : field] ?? fallback;
  };
  return <I18nContext.Provider value={{ lang, locale: LOCALES[lang], setLang, t, pestField, fmtDate }}>{children}</I18nContext.Provider>;
}

export function useI18n() { return useContext(I18nContext); }
