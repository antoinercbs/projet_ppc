from ClientPlayer import ClientPlayer
from Server import Server
from multiprocessing import Process
from tkinter import messagebox, simpledialog
import tkinter
import sys

if __name__ == "__main__":
    NUM_PORT = 8003
    ip = '192.168.43.208'
    nb_player = 0

    root = tkinter.Tk() # initialisation d'une interface pour les choix
    windowWidth = root.winfo_reqwidth() # Centrage de cette interface sur l'écran
    windowHeight = root.winfo_reqheight()
    positionRight = int(root.winfo_screenwidth() / 2 - windowWidth / 2)
    positionDown = int(root.winfo_screenheight() / 2 - windowHeight / 2)
    root.geometry("+{}+{}".format(positionRight, positionDown))
    root.withdraw() # On enlève la fenêtre "fantome" derrière les popups

    is_server = messagebox.askyesno("Freak out !", "Voulez-vous être le serveur de jeu ?")
    if is_server:
        ip = simpledialog.askstring("Freak out !", "Quelle est votre IP à utiliser ?", initialvalue=ip)
        while nb_player < 1 or nb_player > 3:
            nb_player = simpledialog.askinteger("Freak out !", "Combien de joueurs ? (entre 1 et 3)", initialvalue=1)
        nickname = simpledialog.askstring("Freak out !", "Quel est votre pseudo ?", initialvalue='Toto')
        server_process = Process(target=Server, args=(nb_player, ip, NUM_PORT)) # Lancement process server
        client_process = Process(target=ClientPlayer, args=(nickname, ip, NUM_PORT)) # Lancement d'un process client
        server_process.start() # Lancement des process
        client_process.start()
        client_process.join() #Attente de la fin des process
        server_process.join()
    else:
        ip = simpledialog.askstring("Freak out !", "A quelle adresse IP se connecter ?", initialvalue=ip)
        nickname = simpledialog.askstring("Freak out !", "Quel est votre pseudo ?")
        client_process = Process(target=ClientPlayer, args=(nickname, ip, NUM_PORT))
        client_process.start()
        client_process.join()
    print("Arrêt du programme principal.")
    sys.exit()
