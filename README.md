SISTEM DE GESTIUNE SCOLARA CU RECUNOASTERE FACIALA
--------------------------------------------------

Descriere generala:
-------------------
Acest proiect Python este o platforma completa de gestiune scolara, care combina interfete grafice pentru elevi, profesori, diriginti si administratori, cu un sistem de recunoastere faciala pentru pontaj automat.

Functionalitati principale:
---------------------------
 Recunoastere faciala automata pentru elevi, bazata pe imagini stocate local.
 Gestionarea notelor si absentelor prin interfete grafice intuitive.
 Resetarea prezentei dupa 50 de minute pentru a preveni abuzurile.
 Vizualizare in timp real a prezentei elevilor in format grafic.
 Autentificare separata pentru fiecare rol: elev, profesor, diriginte, administrator.
 Posibilitatea de a promova toti elevii automat la sfarsit de an.

Fisiere principale:
-------------------
- face.py .................. Script de recunoastere faciala + pontaj
- elevi.py ................. Dashboard elevi: note + absente
- catalog_profesori.py ..... Catalog interactiv pentru profesori
- catalog_diriginti.py ..... Functii extinse pentru diriginti
- admin.py ................. Panou complet pentru administratori
- school.sql ............... Structura bazei de date (MariaDB/MySQL)
- student_photos/ .......... Folderul cu imaginile elevilor

Cerinte:
--------
- Python 3.10 sau mai nou
- Biblioteci Python:
    - face_recognition
    - opencv-python
    - numpy
    - pymysql
    - pillow
    - tkinter (implicit in majoritatea distributiilor)
- Pachete de sistem (Linux):
    sudo apt install cmake libboost-all-dev libgtk-3-dev

Instalare rapida:
-----------------
1. Instaleaza dependintele:
    pip install face_recognition opencv-python numpy pymysql pillow
2. Creeaza baza de date folosind `school.sql`.
3. Adauga pozele elevilor in folderul `student_photos`.
4. Ruleaza scripturile conform rolului:

   python3 admin.py
   python3 catalog_profesori.py
   python3 catalog_diriginti.py
   python3 elevi.py
   python3 face.py

Extensii planificate:
---------------------
- Numarare obiecte in clasa
- Detectie de flacara in caz de incendiu
- Supraveghere video pe holuri ca masura de securitate
- Notificari automate pentru incidente detectate

Sfaturi utile:
--------------
 Asigura-te ca fiecare elev are o poza clara, frontala.
 Foloseste webcam-uri de calitate pentru o recunoastere mai buna.
 Poti modifica baza de date `school` pentru a adauga noi materii, clase sau utilizatori.
 Pentru recunoastere fara UI, ruleaza `face.py` cu optiunea `--headless`.

Proiect dezvoltat cu scop educativ si didactic.
