EduFace – Sistem Inteligent de Gestiune Școlară

EduFace este o aplicație desktop modulară dezvoltată în Python, care revoluționează modul în care datele educaționale sunt gestionate în școli. Proiectul oferă funcționalități de marcare automată a prezenței cu recunoaștere facială, administrare completă a cataloagelor, vizualizare de note și absențe, precum și promovare automată a elevilor.

Funcționalități principale

Modulul Admin
- Adăugare și editare elevi, profesori, diriginți, clase și materii
- Asociere profesori–materii–clase
- Ștergere de note și absențe
- Vizualizare completă a cataloagelor
- Promovare automată a elevilor (IX–XI)
- Ștergerea automată a elevilor din clasa a XII-a după absolvire

Modulul Profesor
- Autentificare personalizată
- Vizualizarea elevilor cu poze și status de prezență
- Grilă interactivă pentru notare și marcare prezență
- Vizualizarea mediilor și istoricului individual
- Detalii rapide per elev

Modulul Diriginte
- Acces complet la situația clasei: note și absențe
- Ștergere note sau absențe greșite
- Catalog detaliat cu medii generale
- Filtrare după materie și export (în viitor)

Modulul Elev
- Acces personalizat la notele proprii și absențe
- Vizualizare medii și istoric
- Interfață simplă, intuitivă și clară

Modulul de Recunoaștere Facială
- Detectarea automată a fețelor elevilor în timp real
- Marcarea prezenței în baza de date fără intervenție umană
- Resetare automată a prezenței după 50 de minute
- Funcționare locală (inclusiv headless), fără servere externe

Structură Proiect
- admin.py – modul de administrare
- catalog_profesori.py – aplicație pentru profesori
- catalog_diriginti.py – aplicație pentru diriginți
- elevi.py – interfață elevi
- face.py – modulul de recunoaștere facială
- catalog.py – launcher GUI unificat
- school.sql – schema bazei de date
- student_photos/ – folderul cu poze pentru recunoaștere

Cerințe
- Python 3.10 sau mai nou
- MySQL sau MariaDB
- Biblioteci Python:
  pip install pymysql face_recognition opencv-python Pillow numpy
- CMake și dlib (pentru Windows): https://www.lfd.uci.edu/~gohlke/pythonlibs

Rulare Aplicații
Fiecare modul se rulează separat, în funcție de utilizator:
  python admin.py
  python catalog_profesori.py
  python catalog_diriginti.py
  python elevi.py
  python face.py

Configurare Recunoaștere Facială
1. Creează folderul student_photos în directorul principal.
2. Adaugă poze tip buletin, cu fața clară, denumite corespunzător (ex: Popescu_Mihai_11A.jpg).
3. Asigură-te că baza de date are acel nume în coloana photo din tabelul students.

Avantaje
- Securitate locală, fără dependențe de servere externe
- Automatizare completă a prezenței și promovării
- Interfețe intuitive, separate pe roluri
- Costuri zero de utilizare și întreținere
- Modularitate și extensibilitate facilă

Probleme cunoscute
- Aplicația nu pornește? Verifică dacă baza de date rulează și camera este detectată.
- Recunoașterea facială nu funcționează? Verifică imaginea și extensia fișierului.
- Login eșuat? Confirmă existența utilizatorului în tabelul users și atribuirea rolului corect.

Autori
- Trif Mihai-Alexandru
- Lupșe Darius

Coordonator: Prof. Rareș Mircea Muntean

Licență și Resurse
Aplicația folosește:
- face_recognition: https://github.com/ageitgey/face_recognition
- OpenCV: https://opencv.org/
- Tkinter: https://tkdocs.com
- PyMySQL: https://pymysql.readthedocs.io/

Aplicația este distribuită ca software educațional open-source.
