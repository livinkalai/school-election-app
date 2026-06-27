import json, random
posts = {
    "School Pupil Leader (Boys)": ["R A SUJITH SHIVARAM (A1)", "SARAN N (A6)", "PRAVEEN (A6)", "MANGALESH B (A8)"],
    "School Pupil Leader (Girls)": ["SAWMYA GUPTA (A8)", "HARSHITA (A4)", "KANISHKA P K (A1)", "AMIZHTHINI A (A1)", "Sri Priya XI", "Tejasini.S"],
    "TOPAZ CAPTAIN": ["NEELESHAN K (A4)", "VIJAYA RAGAVAN R (A2)", "NISHAN ASVANTHA G (A2)", "SHATHANAA I V (A5)", "SARAN N (A6)", "RATHEESAN. B (A6)", "KAVINYA SRI C (A6)", "VARSHA (A6)", "DEVIKA S (A6)", "MIRUTHUN JAYAN T (A6)", "MOHIT G (A6)", "YAAHUL RANDIARAJ P (A6)", "SANJAY V (A8)", "Karthick.D XI", "Karthick.D-1 XI", "Shamisha IX"],
    "RUBY CAPTAIN": ["VAIBHAV M (A4)", "SANJITH S (A4)", "AAKASH A (A2)", "RIMEL S (A2)", "KIRAN.S (A6)", "VISHWA RUBAN.S (A6)", "ANTO MELVIN.R (A6)", "GOKUL.R (A6)", "DHRISITH KUMAR S (A6)", "VISHAL B (A6)", "SHREE DHAKSAYINI P (A6)", "RITHIKA K (A6)", "KALPANA SRI R (A6)", "SRINITHI V (A6)", "AJAY KUMAR S (A8)"],
    "EMERALD CAPTAIN": ["MUKESH B (A4)", "RAGASHREE S (A2)", "NITIN S (A2)", "YOGA PRASITHA S (A5)", "BAKOOL BABU S (A5)", "PRANAV.K (A6)", "BALAJI.S (A6)", "KANISHKA.S (A6)", "ANNLY DIVINA L(A6)", "SADHANA V (A6)", "PRANEETH P (A6)", "KARTHI K (A6)", "VISHAL A (A8)", "AKSHAYAA V (A9)"],
    "SAPPHIRE CAPTAIN": ["ATHMIKA K (A5)", "KARTHIK K (A6)", "KIRITHIK KUMAR.R (A6)", "DISHAANTH.S (A6)", "THARUN KUMAR.R (A6)", "JAI AKASH.P (A6)", "DEVANATH T K (A6)", "JOSHUA NITHIN R(A6)", "PRANAV NITHILAN S.A (A8)", "JASSIKA SRI T (A9)"],
    "Cultural captain (Boys)": ["MOHAMED SUHAIL S (A4)", "RAGHAV RAM M (A8)"],
    "Cultural captain (Girls)": ["V ANANYA (A1)", "MAGHEEDARA J (A4)", "RIDANYA B (A4)", "JAI AKHITHA K (A9)", "PRADHIKSHA S (A1)", "SRIMATHI A (A5)", "EBINITHA R (A9)"],
    "Sports captain": ["BRIAN OSWALD J (A2)", "CHAKRAVARTHY (A8)", "BENEDICT IMMANUEL M (A8)", "PRAGEETHA R (A5)", "ROSHINI (A8)"],
    "Vice Captain Topaz (Boys)": ["JEGATH KISORE. K", "VINAY KUMAR K", "SANTHOSH KUMAR", "SRIRAM. S", "PRAJIN.M", "NAGAPRAVEEN. V"],
    "Vice Captain Topaz (Girls)": ["DHARSSHWANA.M", "DHIYASHINI.U", "POORVIKA.M", "PRATHIKSHA .D", "SHREYOGHASWITHA", "MADHU DESHINI.S", "DELCINA YAZHINI. R"],
    "Vice Captain Ruby (Boys)": ["AATHESH.G", "MOHAMED  KASIM.K", "JAY PRANESH A.P", "SARAVANA.M", "SAM RICHARDSON. F", "LIVIN JACOB.S", "LAKSHAN.S", "VISHAL KARTHIK.N", "DHIVAGAR.R", "PRAJITH KUMAR.A"],
    "Vice Captain Ruby (Girls)": ["DELINE ARO.A", "NEHA. K", "THAMARAI.I.M", "DHANUSHREE.K", "EESHA.C.K", "REENA JANE.G", "ABINAYA.J", "DIYA DHARSHIKA. S"],
    "Vice Captain Emerald (Boys)": ["SHREE DHARAN.P.V", "SIYAM SANTHOSH.N.S", "JACKUS MATHEW . J", "BALA HARI.J", "NIKHILESH.S", "VIKAS RAJA. J", "AUSTIN.R.", "KABIL CHAKRAVRTHI.A"],
    "Vice Captain Emerald (Girls)": ["SHAMEERA. A", "THANYA SRI MATHEE.D", "DHANYA SRI D", "SHARRNIKHA.P.K", "HARSHINI.K", "KAVINYA J", "HARSHA VARTHINI. R", "AMIRTHA VARSHINI.T", "JAI DHIYASHINI.K", "KANISHKA.T", "NIKITHA MAYURI.S"],
    "Vice Captain Sapphire (Boys)": ["AAKASH. A", "BASIL RAJAN.J", "ASHVANTH R", "SABARISH. S.K", "NAVEEN SANJAY.S.G", "ARAVIND.N", "DHANVANTH  KRISHNAA.P", "MOHAMMED  FAYAZ.J", "DHIVYA VIGNESH.V"],
    "Vice Captain Sapphire (Girls)": ["DIVYA  RAKSHANA.S.K", "AFRA FATHIMA.M", "MITHUNA RAGAVI.J.K", "NIRUPHAMA.K.M", "GAYATHRI V.K", "DHANYA  LAKSHMI.V", "SABARI SHRI.P"],
}
images = ["Aasimiya IX", "Abila XI", "Alagar.K IX", "Aruna IX", "Aswanth Karthi IX", "Balamurugan IX", "Chandrasekaran.S XI", "Dharshini XI", "Dhiyashini IX", "Dikshita R.J IX", "Elango XI", "Gritharan XI", "Hanifa XI", "Hemavathi IX", "Jai Rakshan IX", "Kanchana IX", "Karthick.D XI", "Khirthiga XI", "Mathivathani IX", "Nithya Jency XI", "Prasath.P.E XI", "Praveen XI", "Priyanga XI", "Ragu.J IX", "Rengarajan XI", "Rishika XI", "RIYA RS -VIII ", "Sarvesh IX", "Satheesh Kumar IX", "Shamisha IX", "Soundarya XI", "Sri Priya XI", "Suresh Aps XI", "Suresh Mdu IX", "Tejasini.S"]
existing = {n for v in posts.values() for n in v}
to_add = [n for n in images if n not in existing]
random.seed(42)
random.shuffle(to_add)
keys = list(posts.keys())
for i, n in enumerate(to_add):
    posts[keys[i % len(keys)]].append(n)
out = json.dumps(posts, indent='\t', ensure_ascii=False)
path = r'D:\Backup\Learn\AI\ElectionApp\School Election App - Src\settings\candidates.json'
with open(path, 'w', encoding='utf-8') as f:
    f.write(out)
print(out)
