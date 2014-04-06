import smtplib
import urllib.request
import urllib.parse
import re
import http.cookiejar
import pickle
from email.mime.text import MIMEText

login ="nom_pre" #Tapez ici votre login de supelec
mdp ="mdpsdesupelec" #Ici le mot de passe supelec
loginMail = "prenom.nom" #Ici votre login du rezo
mdpMail = "mdpDuRezo" #Et votre mot de passe du rezo


# Fonction finale se sers d'un json pour récuper les utilisateurs
def alerteENT(login,mdp,loginMail,mdpMail) :
	page = connexionENT(login,mdp)

	page = reduction(page)

	liste = compare(page)

	envoyerMail(liste,loginMail,mdpMail)


#Fonction se connectant a l'ENT Supelec grace au login et au mot de passe et revoyant la page sous forme de string
def connexionENT(login,mdp):
	urlLogin="http://portail-appliweb.supelec.fr:81/ENT/Connexion.aspx?ReturnUrl=%2fENT%2fDefault.aspx"
	urlNotes="http://portail-appliweb.supelec.fr:81/Choix/Resulcourant.aspx"
	viewstate="dDw3MDUzNDg1NDt0PDtsPGk8MT47PjtsPHQ8O2w8aTwxMD47aTwxMz47aTwxNT47aTwxNz47aTwxOT47aTwyMT47PjtsPHQ8cDw7cDxsPG9ua2V5KmRvd247PjtsPGphdmFzY3JpcHQ6aWYoKGV2ZW50LndoaWNoICYmIGV2ZW50LndoaWNoID09IDEzKSB8fCAoZXZlbnQua2V5Q29kZSAmJiBldmVudC5rZXlDb2RlID09MTMpKXtldmVudC5rZXlDb2RlPTlcO31lbHNlIHJldHVybiB0cnVlXDs7Pj4+Ozs+O3Q8cDw7cDxsPG9ua2V5KmRvd247PjtsPGphdmFzY3JpcHQ6aWYoKGV2ZW50LndoaWNoICYmIGV2ZW50LndoaWNoID09IDEzKSB8fCAoZXZlbnQua2V5Q29kZSAmJiBldmVudC5rZXlDb2RlID09MTMpKXtCdENvbm5leGlvbi5DbGljaygpXDt9Oz4+Pjs7Pjt0PHA8cDxsPFZpc2libGU7PjtsPG88Zj47Pj47Pjs7Pjt0PHA8cDxsPFZpc2libGU7PjtsPG88Zj47Pj47Pjs7Pjt0PHA8cDxsPFZpc2libGU7PjtsPG88Zj47Pj47Pjs7Pjt0PHA8cDxsPFZpc2libGU7PjtsPG88Zj47Pj47Pjs7Pjs+Pjs+Pjs+sNV/WrqDOPaKsy8zINqFVF5DDE8="
	Bt ="Se+connecter+à+l'ENT"

	#On récupère les cookies indipensable à la connexion
	CookieProcessor=urllib.request.HTTPCookieProcessor()

	#On construit les requètes : la première sans rien et la deuxième avec les infos
	data = urllib.parse.urlencode({'__VIEWSTATE':viewstate, 'Utilisateur':login, 'MotdePasse':mdp, 'BtConnexion':Bt})
	data = data.encode('utf-8')
	req1 = urllib.request.Request(url=urlLogin)
	req2 = urllib.request.Request(url=urlLogin,data=data)
	req2.add_header("Content-Type","application/x-www-form-urlencoded;charset=utf-8")

	# On construit l'opener
	opener = urllib.request.build_opener(CookieProcessor)
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]

	opener.open(req1)

	opener.open(req2)

	g=opener.open(urlNotes)

	#On retourne la page sous forme de texte
	page = g.read().decode('utf-8')
	return page

#Fonction netoyant la page de toute les balises et lignes inutiles
def reduction(page) :

	page = re.sub('<[^<]+?>', '', page)
	page = re.sub('(&nbsp;)?\t?\r?', '', page)

	search = re.search("Moyenne des modules obligatoires : ",page)

	page=page[0:search.start()]

	search = re.search("ECTS",page)
	page=page[search.end():]

	return page


# Fonction recevant la page netoyée et retournant la liste des nom d'electifs alternés avec leurs notes
def notesElectif(page) :
	liste =[]
	for i in range(1, 5) :
		pattern = re.compile("Electif([A-Za-z éêè'])+" + str(i))
		search = pattern.search(page)
		j = 1
		while search :
			end=search.end()
			#liste.append(page[search.start()+7:search.end()-1]+" Seq"+page[end-1])
			#liste.append(floatNote(page[end:end+6]))
			liste.append(page[search.start()+7:search.end()-1]+" Seq"+page[end-1]+" : "+floatNote(page[end:end+6]))
			search = pattern.search(page, search.end() )
			j+=1
	return liste


# Fonction recevant la page netoyée et retournant la liste des nom de modules obligatoires alternés avec leurs notes
def notesOblig(page) :
	liste = []
	for i in range(1, 5) :
		pattern = re.compile("Oblig([A-Za-zéèê '])+(- [1-9])?" + str(i))
		search = pattern.search(page)
		while search :
			end=search.end()
			liste.append(page[search.start()+5:search.end()-1]+" Seq"+page[end-1]+" : "+floatNote(page[end:end+5]))
			#liste.append(floatNote(page[end:end+5]))
			search = pattern.search(page, search.end() )
	return liste


#Fonction reperant si une note est de la forme 11 ou 11.50 et retourne la string adaptée
def floatNote(string) :
	if len(string)>6 :
		return "problème float note"
	elif string[1]=="," :
		return string[0]
	elif string[2]=="," :
		return string
	else :
		return string[0:2]



# Fonction comparant les liste de notes sauvegardée et en temps reel pour retourner la liste de difference
def compare(page) :
	
	listeSite = notesElectif(page) + notesOblig(page)
	liste = []

	#On essaiye d'ouvrir le fichier, si il n'existe pas on le crée et on revoie toutes les notes
	try:
		listeSave = pickle.load(open('save.p', 'rb'))
	except (IOError,EOFError):
		pickle.dump(listeSite,open('save.p','wb'))
		return listeSite


	for i in range(0, len(listeSave)-1) :

		if listeSite[i]!=listeSave[i] :
			listeSave.insert(i,listeSite[i])
			liste.append(listeSite[i])

	for i in range(len(listeSave), len(listeSite)) :
	 	liste.append(listeSite[i])


	pickle.dump(listeSite,open('save.p','wb'))
	return liste




#Fonction qui envoie  un mail avec les notes
def envoyerMail(liste, login, mdp) :
	if len(liste) != 0 :
		server = smtplib.SMTP_SSL('smtp.larez.fr')
		server.login(login, mdp)
		msg = MIMEText(ecrireNotes(liste))
		msg['Subject'] = "Nouvelle notes"
		msg['From'] = 'antoine.rabany@larez.fr'
		msg['To'] = login + '@supelec.fr'
		server.send_message(msg)
		server.quit()
		print("mail envoyé")

#Fonction qui écrit les notes finalement
def ecrireNotes(liste) :
	str = ""
	for i, elt in enumerate(liste) :
		str += elt+"\n"
	return str


alerteENT(login,mdp,loginMail,mdpMail)
