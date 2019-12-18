from ClientPlayer import ClientPlayer
from Server import Server
from multiprocessing import Process
from tkinter import messagebox, simpledialog

if __name__ == "__main__":
    NUM_PORT = 80
    Ip = '127.0.0.1'
    nb_player = 0
    is_server = messagebox.askyesno("Freak out !", "Voulez-vous être le serveur de jeu ?")
    if is_server:
        ip = simpledialog.askstring("Freak out !", "Quelle est votre IP à utiliser ?")
        while nb_player < 1 or nb_player > 3:
            nb_player = simpledialog.askinteger("Freak out !", "Combien de joueurs ? (entre 1 et 3)")
        nickname = simpledialog.askstring("Freak out !", "Quel est votre pseudo ?")
        server_process = Process(target=Server, args=(nb_player, ip, NUM_PORT))
        client_process = Process(target=ClientPlayer, args=(nickname, ip, NUM_PORT))
        server_process.start()
        client_process.start()
        client_process.join()
        server_process.join()
    else:
        ip = simpledialog.askstring("Freak out !", "A quelle adresse IP se connecter ?")
        nickname = simpledialog.askstring("Freak out !", "Quel est votre pseudo ?")
        client_process = Process(target=ClientPlayer, args=(nickname, ip, NUM_PORT))
        client_process.start()
        client_process.join()

