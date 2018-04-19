import sys, os

import lexer as ssp

#C1="ps -aux | sort -k1n 2>> /dev/null | tr 'a-z' 'A-Z' | tee toto.txt | cat > log.txt "
#C1="ps -aux | sort -k1n | wc -l"
print("******************* PROGRAMME MINI-SHELL *******************\n")
print("\t")
#result = ssp.get_parser().parse(C1)


#def execpipe(inp,output,command):
def executerLesPipes(rfd,wfd,command): # fonction permet d'executer une commande à en lecture ds le rfd et ecrire vers wfd
      pid = os.fork()
      if pid == 0: # le fils s'occope de l'execution des commandes
            commande=command._cmd.getCommand() # pour recuperer les commandes à partir de l'objet PROCESS du lexer
            argCommande=command._cmd.getArgs()
            argCommande = [commande]+argCommande # on rajoute la commande en premier puis l'argument : toute les fn exec le 1er arg est la commande lui meme
            if rfd != 0: # on verifie si il y a lecture venant de l'entrer standard
                  os.dup2(rfd,0)# on lu depuis rfd au lieu de l'entrer standard
                  os.close(rfd)# on fermer apres
            else:
                  redirEntree = filtrerRedirectionsEntree(command) # on cherche si il y a une redirection dans la commande
                  if redirEntree:
                        re = os.open(redirEntree._filespec, os.O_RDONLY)
                        os.dup2(re, 0)
                        os.close(re)

            if wfd != 1: # si on a une sortie vers le tube
                  os.dup2(wfd,1) # au lieu de la sortie standard au ecrit vers wfd
                  os.close(wfd) # on ferme
            else :
                  redirSortie = filtrerRedirectionsSortie(command) # on cherche si on a une redirection de sortie dans la commande
                  if redirSortie:
                        re_wr_fd = None # on initialise
                        if redirSortie.isAppend(): # si c'est en mode Append on ouvre en mode append
                              re_wr_fd=os.open(redirSortie._filespec, os.O_WRONLY | os.O_APPEND | os.O_CREAT )
                        else: # sinon on fait une redirection normale
                              re_wr_fd=os.open(redirSortie._filespec, os.O_WRONLY| os.O_CREAT | os.O_TRUNC)
                        os.dup2(re_wr_fd, 1)
                        os.close(re_wr_fd)

                  redirErreur=filtrerRedirectionsErreur(command)# redirection d'erreur gerer par le fils
                  if redirErreur:
                        re_Er_fd = None
                        if redirErreur.isAppend():
                              re_Er_fd=os.open(redirErreur._filespec, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
                        else:
                              re_Er_fd=os.open(redirErreur._filespec, os.O_WRONLY| os.O_CREAT | os.O_TRUNC)

                        os.dup2(re_Er_fd,2)
                        os.close(re_Er_fd)


            try:
                os.execvp(commande,argCommande)
            except Exception as e:
                os.write(2,bytearray("Il y a un probleme avec l'execution de " +commande +"\n","utf-8"))
                sys.exit(-1)

      else: # le père  attend la mort du fils

            os.waitpid(pid, 0)


def executer(p): # p c'est l'objet process cette permet d'executer la commande
      rfd = 0
      for i in p:
            r,w = os.pipe()
            executerLesPipes(rfd,w,i)
            os.close(w)
            rfd = r # entrer du tube courant  et rfd entree du tube precedent
      pid = os.fork()
      if pid == 0:
          if rfd != 0:
            os.dup2(rfd,0)

            dernierCommande = p[-1]._cmd.getCommand() # on prend la dernière commande la chaine et on execute
            dernierArgs =  p[-1]._cmd.getArgs() # on prend dernier argument
            dernierArgs = [dernierCommande] + dernierArgs
            redirSortie = filtrerRedirectionsSortie(p[-1]) # on redirige la derniere commande vers la sortie
            if redirSortie:
                  re_wr_fd = None
                  if redirSortie.isAppend():
                        re_wr_fd=os.open(redirSortie._filespec, os.O_WRONLY | os.O_APPEND | os.O_CREAT )
                  else:
                        re_wr_fd=os.open(redirSortie._filespec, os.O_WRONLY| os.O_CREAT | os.O_TRUNC)
                  os.dup2(re_wr_fd, 1)
                  os.close(re_wr_fd)

            """ Partie pour faire la redirection d'erreur """

            redirErreur=filtrerRedirectionsErreur(p[-1])# redirection d'erreur gerer par le fils
            if redirErreur:
                  re_Er_fd = None
                  if redirErreur.isAppend():
                        re_Er_fd=os.open(redirErreur._filespec, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
                  else:
                        re_Er_fd=os.open(redirErreur._filespec, os.O_WRONLY| os.O_CREAT | os.O_TRUNC)

                  os.dup2(re_Er_fd,2)
                  os.close(re_Er_fd)

            try:
                os.execvp(dernierCommande, dernierArgs)
            except Exception as e:
                os.write(2,bytearray("Il y a un probleme avec l'execution de " + dernierCommande +"\n","utf-8"))
                sys.exit(-1)
      os.wait()
      return
"""********************** Fin redirection erreur ************************************** """

""" filtrer la redirection d'entree à partir d'un Processus """
def filtrerRedirectionsEntree(processus): # procesus c'est un obet de la class PROCESS(): du lexer.py
      if not processus._redirs or  not processus._redirs._redirs : # si il n'y pas de redirection renvoi None
            return None
      return  next((re for re in processus._redirs._redirs if re.__class__.__name__ == "INREDIR"), None) # return la 1ere valeur dans une liste qui valide une condition, si aucun elt ne valid la condition le 2 arg est renvoyer

""" filtrer la redirection sortie à partir d'un Processus """
def filtrerRedirectionsSortie(processus):
      if not processus._redirs or not processus._redirs._redirs:
            return None
      return  next((re for re in processus._redirs._redirs if re.__class__.__name__ == "OUTREDIR"), None)

""" filtrer la redirection erreur à partir d'un Processus """
def filtrerRedirectionsErreur(processus):
      return  next((re for re in processus._redirs._redirs if re.__class__.__name__ == "ERRREDIR"), None)

# ******************************Fin *************************************

""" fonction Principale """

#print(commandes)

while(True): # on fait une boucle infini pour excuter des commande à partir du prompt
      C = input("\nlinux$")
      if C.strip()=="": # si il n'y a une ligne vide ou space passe et continue avec pour retourner à l'etape 1
          continue
      TableauCommande = ssp.get_parser().parse(C)

      executer(TableauCommande)
