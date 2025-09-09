#from .serializers import UserSerializer
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db import connection, OperationalError,IntegrityError
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
#from .serializers import LoginSerializer
from django.contrib.auth.hashers import check_password
from rest_framework.permissions import IsAuthenticated
import random
import os
import resend, requests
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser

def generate_access_code():
    """Génère un code d'accès unique à 4 chiffres."""
    return str(random.randint(1000, 9999))


def resend_send_email(user_name, user_email, access_code):

    resend.api_key = "re_dyNqqhiX_HQANV3AfxJdjwqEgxERKuMbK"

    params: resend.Emails.SendParams = {
        "from": "Acme <onboarding@resend.dev>",
        "to": [user_email],
        "subject": "hello world",
        "html": f"Bonjour {user_name}, <br/><br/>Votre code d\'accès est le suivant : <strong>{access_code}</strong>.<strong>Ne le communiquez à personne</strong>.",
    }

    email = resend.Emails.send(params)
    
    #email: resend.Emails.SendResponse = resend.Emails.send(params)
    #print(email)

def unplunk_send_email(user_name, user_email, access_code):
    requests.post(
        "https://api.useplunk.com/v1/send",
        headers={"Content-Type": "application/json", "Authorization": "Bearer sk_e018919f0784429c320ea75de1a997e4e665a39395160a5c"},
        json={
        "subject": "Your first email",
        #"body": "Hello from Plunk!", 
        "body": f"Bonjour {user_name}, <br/><br/>Votre code d\'accès est le suivant : <strong>{access_code}</strong>.<strong>Ne le communiquez à personne</strong>.",
        "to": f"{user_email}", 
        },
    )

# Dictionnaire qui mappe un "endpoint name" à une requête SQL
# Plus tard, ajouter cela dans .env
PREDEFINED_QUERIES = {
    "projects": "SELECT * FROM employees LIMIT 10;",
    "sites": "SELECT * FROM api_site LIMIT 10;",
    "contracts": "SELECT * FROM api_contract LIMIT 10;",
    "employees": "SELECT * FROM employees LIMIT 5;",
    # d'autres tables à ajouter plus tard ici...
}

@api_view(["GET"])
def db_connectivity(request):
    """
    Endpoint pour tester la connexion à la base de données.
    Retourne 'ok' si la connexion fonctionne, sinon 'error'.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        return Response({"status": "ok", "message": "Connexion DB réussie ✅"})
    except OperationalError as e:
        return Response({"status": "error", "message": str(e)}, status=500)


@api_view(["GET"])
def run_select_query(request):
    """
    Endpoint pour exécuter une requête SELECT SQL.
    Exemple body JSON : { "query": "SELECT * FROM employees LIMIT 5;" }
    """
    query = "SELECT * FROM employees LIMIT 5;"

    if not query: #or not query.strip().lower().startswith("select")
        return Response(
            {"error": "Seules les requêtes SELECT sont autorisées."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # Transformer les résultats en liste de dictionnaires
        results = [dict(zip(columns, row)) for row in rows]

        return Response({"status": "ok", "results": results})

    except OperationalError as e:
        return Response({"status": "error", "message": str(e)}, status=500)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)
    

@api_view(["GET"])
def get_users_query(request):
    """
    Endpoint qui exécute un SELECT sur la table 'api_project' et retourne les résultats.
    La requête SQL est définie côté serveur.
    """
    # Requête SQL prédéfinie
    sql = "SELECT * FROM employees;"
    try:
        with connection.cursor() as cursor:
            
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # Transformer le résultat en liste de dictionnaires
        results = [dict(zip(columns, row)) for row in rows]

        return Response({"status": "ok", "results": results})

    except OperationalError as e:
        return Response({"status": "error", "message": str(e)}, status=500)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)

@api_view(["GET"])
def run_predefined_query(request, query_name):
    """
    Endpoint qui exécute une requête SQL prédéfinie.
    L'utilisateur choisit le query_name dans l'URL.
    """
    sql = PREDEFINED_QUERIES.get(query_name)

    if not sql:
        return Response(
            {"status": "error", "message": f"Aucune requête trouvée pour '{query_name}'"},
            status=400
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
        results = [dict(zip(columns, row)) for row in rows]

        return Response({"status": "ok", "results": results})

    except OperationalError as e:
        return Response({"status": "error", "message": str(e)}, status=500)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)


@api_view(["POST"])
def register_user(request):
    """
    Endpoint pour créer un nouvel utilisateur.
    Body JSON attendu :
    {
        "username": "utilisateur1",
        "email": "email@example.com",
        "password": "MotDePasse123"
    }
    """
    data = request.data
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Validation simple
    if not username or not email or not password:
        return Response(
            {"status": "error", "message": "username, email et password requis"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"status": "error", "message": "username déjà utilisé"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"status": "error", "message": "email déjà utilisé"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Création de l'utilisateur
    user = User.objects.create_user(username=username, email=email, password=password)
    user.save()

    # Génération du token JWT
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    return Response({
        "status": "ok",
        "message": f"Utilisateur '{username}' créé avec succès",
        "access_token": access_token,
        "refresh_token": refresh_token
    })

    #return Response(
    #    {"status": "ok", "message": f"Utilisateur '{username}' créé avec succès"}
    #)


@api_view(["POST"])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({"message": "Utilisateur créé avec succès", "id": user.id}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def register_user_postgres(request):
    """
    Endpoint pour enregistrer un utilisateur dans PostgreSQL via INSERT
    et renvoyer JWT.
    JSON attendu :
    {
        "username": "utilisateur_pg",
        "email": "user_pg@example.com",
        "password": "MotDePasse123"
    }
    """
    data = request.data
    fname = data.get("fname")
    lname = data.get("lname")
    user_email = data.get("email")
    role = data.get("role")
    password = data.get("password")

    if not all([fname, lname, role, password, user_email]):
        return Response({"status": "error", "message": "Tous les champs sont requis"},
                        status=status.HTTP_400_BAD_REQUEST)

    

    try:
        hashed_password = make_password(password)  # hachage sécurisé
        # Générer un code unique
        access_code = None


        while True:
            code = generate_access_code() # encrypt this code
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM users WHERE access_code = %s", [code])
                exists = cursor.fetchone()
            if not exists:
                access_code = code
                break


        with connection.cursor() as cursor:
            # INSERT dans users_table
            cursor.execute("""
                INSERT INTO users (fname, lname, role,password, access_code)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, [fname, lname, role,hashed_password, access_code])

            user_id = cursor.fetchone()[0]
            #resend_send_email(fname,user_email,access_code)
            unplunk_send_email(fname,user_email,access_code)
            return Response({
                "status": "ok",
                "message": f"Utilisateur '{fname}' créé dans PostgreSQL",
                #"access_token": access_token,
                #"refresh_token": refresh_token
            })
        
    except IntegrityError as e:
        return Response({"status": "error", "message": "username ou email déjà utilisé"},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"status": "error", "message": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

        # DummyUser pour générer le JWT
        #class DummyUser:
        #    def __init__(self, user_id, fname,lname,role, **args):
        #        self.id = user_id
        #        self.fname = fname
        #        self.is_active = True
        #        self.is_staff = False
        #        self.is_superuser = False

        #dummy_user = DummyUser(user_id, fname, lname, role)

        #refresh = RefreshToken.for_user(dummy_user)

        #return Response({
            #"refresh": str(refresh),
        #    "access": str(refresh.access_token),
        #    "user": {
        #        "id": user_id,
        #        "fname": fname,
        #        "lname": lname,
        #        "role": role
        #    }
        #}, status=status.HTTP_201_CREATED)

        # Générer le token JWT
        # Ici on crée un token "custom" basé sur user_id et username
        # car nous n'utilisons pas Django User model
        #payload_user = type('UserDummy', (object,), {"id": user_id, "fname": fname})
        #refresh = RefreshToken.for_user(payload_user)
        #access_token = str(refresh.access_token)
        #refresh_token = str(refresh)


@api_view(["POST"])
def login_user(request):
    """
    Login utilisateur avec fname + password
    (table Postgres 'users' : id, fname, lname, role, password)
    """
    fname = request.data.get("fname")
    password = request.data.get("password")

    if not fname or not password:
        return Response({"error": "fname et password sont requis"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE fname = %s", [fname])
            row = cursor.fetchone()

        if row is None:
            return Response({"error": "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)

        user_id, db_fname, db_lname, db_role, db_password = row

        # Vérification du mot de passe
        if not check_password(password, db_password):
            return Response({"error": "Mot de passe incorrect"}, status=status.HTTP_401_UNAUTHORIZED)

        # Générer JWT manuellement (user fictif, car pas lié à Django User)
        class DummyUser:
            def __init__(self, id, fname, role):
                self.id = id
                self.fname = fname  # SimpleJWT demande un username
                self.role = role
                self.is_active = True
                self.is_staff = False
                self.is_superuser = False

        dummy_user = DummyUser(user_id, db_fname, db_role)
        refresh = RefreshToken.for_user(dummy_user)

        return Response({
            #"refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user_id,
                "fname": db_fname,
                "lname": db_lname,
                "role": db_role,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": f"Bonjour {request.user}, tu es authentifié ✅"})

@api_view(["POST"])
def login_view(request):
    """
    Login utilisateur avec username + password
    Retourne un token JWT (refresh + access) + infos utilisateur
    """
    fname = request.data.get("fname")
    password = request.data.get("password")

    if not fname or not password:
        return Response({"error": "Username et password requis"}, status=status.HTTP_400_BAD_REQUEST)

    hashed_password = make_password(password)

    user = authenticate(username=fname, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.fname,
                "last_name": user.lname,
                "is_staff": user.is_staff,
            }
        })
    else:
        return Response({"error": "Identifiants invalides"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
def login_path(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "fname": user.fname,
                "lname": user.lname,
                #"is_staff": user.is_staff,
                #"is_superuser": user.is_superuser,
            }
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["POST"])
def login_with_code(request):
    """
    Connexion via access_code uniquement.
    Retourne un JWT + infos utilisateur.
    """
    access_code = request.data.get("access_code")

    if not access_code:
        return Response({"error": "Le code d'accès est requis"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, fname, lname, role FROM users WHERE access_code = %s",
                [access_code]
            )
            user = cursor.fetchone()

        if not user:
            return Response({"error": "Code d'accès invalide"}, status=status.HTTP_401_UNAUTHORIZED)

        user_id, fname, lname, role = user

        # DummyUser pour JWT
        class DummyUser:
            def __init__(self, id, username):
                self.id = id
                self.username = username
                self.is_active = True
                self.is_staff = False
                self.is_superuser = False

        dummy_user = DummyUser(user_id, fname)

        refresh = RefreshToken.for_user(dummy_user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user_id,
                "fname": fname,
                "lname": lname,
                "role": role,
                "access_code": access_code
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(["POST"])
def assign_missions(request):
    """
    Crée une nouvelle demande de recrutement dans la base de données.
    """
    data = request.data
    project = data.get("project")
    mission_type = data.get("mission_type")
    people_count = data.get("people_count")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    urgency_level = data.get("urgency_level")
    special_instructions = data.get("special_instructions", "")

    if not all([project, mission_type, people_count, start_date, end_date, urgency_level]):
        return Response({"error": "Tous les champs obligatoires doivent être remplis."}, 
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO mission_assignments 
                (project, mission_type, people_count, start_date, end_date, urgency_level, special_instructions)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                [project, mission_type, people_count, start_date, end_date, urgency_level, special_instructions]
            )
            new_id = cursor.fetchone()[0]

        return Response({
            "message": "Demande de recrutement créée avec succès",
            "request_id": new_id,
            "data": data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def create_employee(request):
    """
    Crée un employé avec tous les champs (infos personnelles, professionnelles et documents).
    """
    data = request.data

    # Champs personnels
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    nationality = data.get("nationality")
    birth_date = data.get("birth_date")
    birth_place = data.get("birth_place")
    full_address = data.get("full_address")
    phone = data.get("phone")
    email = data.get("email")
    emergency_contact_name = data.get("emergency_contact_name", "")
    emergency_contact_phone = data.get("emergency_contact_phone", "")

    # Champs professionnels précédents
    job_type = data.get("job_type")  # CDI, CDD, Intérim
    diploma = data.get("diploma", "")
    additional_training = data.get("additional_training", "")
    professional_certificate = data.get("professional_certificate", "")
    spoken_languages = data.get("spoken_languages", "")
    language_level = data.get("language_level")  # B2, A1, A2

    # Nouveaux champs
    current_position = data.get("current_position", "")
    company = data.get("company", "")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    moral_reference = data.get("moral_reference", "")
    employment_type_field = data.get("employment_type")  # CDI, CDD, Intérim
    hire_date = data.get("hire_date")
    department = data.get("department", "")
    base_salary = data.get("base_salary")
    bonuses = data.get("bonuses", "")
    probation_period = data.get("probation_period")

    # Gestion fichiers
    certificate_file = None
    portfolio_file = None

    if "certificate_file" in request.FILES:
        file_obj = request.FILES["certificate_file"]
        file_path = f"uploads/certificates/{file_obj.name}"
        with open(file_path, "wb+") as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        certificate_file = file_path

    if "portfolio_file" in request.FILES:
        file_obj = request.FILES["portfolio_file"]
        file_path = f"uploads/portfolio/{file_obj.name}"
        with open(file_path, "wb+") as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        portfolio_file = file_path

    # Vérification des champs obligatoires
    required_fields = [first_name, last_name, nationality, birth_date, birth_place, full_address, phone, email, job_type, language_level]
    if not all(required_fields):
        return Response({"error": "Tous les champs obligatoires doivent être remplis."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO employees
                (first_name, last_name, nationality, birth_date, birth_place, full_address, phone, email,
                 emergency_contact_name, emergency_contact_phone,
                 job_type, diploma, certificate_file, additional_training, professional_certificate,
                 spoken_languages, language_level,
                 current_position, company, start_date, end_date, moral_reference, portfolio_file,
                 employment_type, hire_date, department, base_salary, bonuses, probation_period)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                [first_name, last_name, nationality, birth_date, birth_place, full_address, phone, email,
                 emergency_contact_name, emergency_contact_phone,
                 job_type, diploma, certificate_file, additional_training, professional_certificate,
                 spoken_languages, language_level,
                 current_position, company, start_date, end_date, moral_reference, portfolio_file,
                 employment_type_field, hire_date, department, base_salary, bonuses, probation_period]
            )
            new_id = cursor.fetchone()[0]

        return Response({
            "message": "Employé ajouté avec succès",
            "employee_id": new_id,
            "data": data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def create_leave_request(request):
    """
    Ajoute une demande de congés dans la base de données.
    """
    data = request.data
    employee_id = data.get("employee_id")
    leave_type = data.get("leave_type")  # maladie, annuel, maternité
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    address_during_leave = data.get("address_during_leave")
    contact_phone = data.get("contact_phone")

    # Vérification des champs obligatoires
    required_fields = [leave_type, start_date, end_date, address_during_leave, contact_phone]
    if not all(required_fields):
        return Response({"error": "Tous les champs obligatoires doivent être remplis."}, 
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO leave_requests
                (employee_id, leave_type, start_date, end_date, address_during_leave, contact_phone)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                [employee_id, leave_type, start_date, end_date, address_during_leave, contact_phone]
            )
            new_id = cursor.fetchone()[0]

        return Response({
            "message": "Demande de congé ajoutée avec succès",
            "leave_request_id": new_id,
            "data": data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def create_recruitment_request(request):
    """
    Ajoute une demande de recrutement dans la base de données.
    """
    data = request.data
    type_poste = data.get("type_poste")          # CDI, CDD, Intérim
    job_title = data.get("job_title")
    proposed_salary = data.get("proposed_salary")
    requesting_service = data.get("requesting_service")
    start_date = data.get("start_date")
    message = data.get("message", "")
    status_field = data.get("status")            # Normal, Urgent, Critique

    # Vérification des champs obligatoires
    required_fields = [type_poste, job_title, proposed_salary, requesting_service, start_date, status_field]
    if not all(required_fields):
        return Response({"error": "Tous les champs obligatoires doivent être remplis."}, 
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO recruitment_requests
                (type_poste, job_title, proposed_salary, requesting_service, start_date, message, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                [type_poste, job_title, proposed_salary, requesting_service, start_date, message, status_field]
            )
            new_id = cursor.fetchone()[0]

        return Response({
            "message": "Demande de recrutement ajoutée avec succès",
            "recruitment_request_id": new_id,
            "data": data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







