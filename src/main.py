import schedule
import subprocess

from art import *
from cache import *
from utils import *
from config import *
from status import *
from uuid import uuid4
from constants import *
from classes.Tts import TTS
from termcolor import colored
from classes.Twitter import Twitter
from classes.YouTube import YouTube
from prettytable import PrettyTable
from classes.Outreach import Outreach
from classes.AFM import AffiliateMarketing
from llm_provider import list_models, select_model, get_active_model

def main():
    """Main entry point for the application, providing a menu-driven interface
    to manage YouTube, Twitter bots, Affiliate Marketing, and Outreach tasks.

    This function allows users to:
    1. Start the YouTube Shorts Automater to manage YouTube accounts, 
       generate and upload videos, and set up CRON jobs.
    2. Start a Twitter Bot to manage Twitter accounts, post tweets, and 
       schedule posts using CRON jobs.
    3. Manage Affiliate Marketing by creating pitches and sharing them via 
       Twitter accounts.
    4. Initiate an Outreach process for engagement and promotion tasks.
    5. Exit the application.

    The function continuously prompts users for input, validates it, and 
    executes the selected option until the user chooses to quit.

    Args:
        None

    Returns:
        None"""

    # Get user input
    # user_input = int(question("Select an option: "))
    valid_input = False
    while not valid_input:
        try:
    # Show user options
            info("\n============ OPCIONES ===========", False)

            for idx, option in enumerate(OPTIONS):
                print(colored(f" {idx + 1}. {option}", "cyan"))

            info("=================================\n", False)
            user_input = input("Seleccioná una opción: ").strip()
            if user_input == '':
                print("\n" * 100)
                raise ValueError("No se permite una entrada vacía.")
            user_input = int(user_input)
            valid_input = True
        except ValueError as e:
            print("\n" * 100)
            print(f"Entrada inválida: {e}")


    # Start the selected option
    if user_input == 1:
        info("Iniciando automatización de YT Shorts...")

        cached_accounts = get_accounts("youtube")

        if len(cached_accounts) == 0:
            warning("No se encontraron cuentas en caché. ¿Querés crear una ahora?")
            user_input = question("Sí/No: ")

            if user_input.lower() in ("sí", "si", "yes"):
                generated_uuid = str(uuid4())

                success(f" => ID generado: {generated_uuid}")
                nickname = question(" => Ingresá un apodo para esta cuenta: ")
                fp_profile = question(" => Ingresá la ruta al perfil de Firefox: ")
                niche = question(" => Ingresá el nicho de la cuenta: ")
                language = question(" => Ingresá el idioma de la cuenta: ")

                account_data = {
                    "id": generated_uuid,
                    "nickname": nickname,
                    "firefox_profile": fp_profile,
                    "niche": niche,
                    "language": language,
                    "videos": [],
                }

                add_account("youtube", account_data)

                success("¡Cuenta configurada exitosamente!")
        else:
            table = PrettyTable()
            table.field_names = ["ID", "UUID", "Apodo", "Nicho"]

            for account in cached_accounts:
                table.add_row([cached_accounts.index(account) + 1, colored(account["id"], "cyan"), colored(account["nickname"], "blue"), colored(account["niche"], "green")])

            print(table)
            info("Escribí 'd' para eliminar una cuenta.", False)

            user_input = question("Seleccioná una cuenta para iniciar (o 'd' para eliminar): ").strip()

            if user_input.lower() == "d":
                delete_input = question("Ingresá el número de cuenta a eliminar: ").strip()
                account_to_delete = None

                for account in cached_accounts:
                    if str(cached_accounts.index(account) + 1) == delete_input:
                        account_to_delete = account
                        break

                if account_to_delete is None:
                    error("Cuenta seleccionada inválida. Intentá de nuevo.", "red")
                else:
                    confirm = question(f"¿Estás seguro de que querés eliminar '{account_to_delete['nickname']}'? (Sí/No): ").strip().lower()

                    if confirm in ("sí", "si", "yes"):
                        remove_account("youtube", account_to_delete["id"])
                        success("¡Cuenta eliminada exitosamente!")
                    else:
                        warning("Eliminación de cuenta cancelada.", False)

                return

            selected_account = None

            for account in cached_accounts:
                if str(cached_accounts.index(account) + 1) == user_input:
                    selected_account = account

            if selected_account is None:
                error("Cuenta seleccionada inválida. Intentá de nuevo.", "red")
                main()
            else:
                youtube = YouTube(
                    selected_account["id"],
                    selected_account["nickname"],
                    selected_account["firefox_profile"],
                    selected_account["niche"],
                    selected_account["language"]
                )

                while True:
                    rem_temp_files()
                    info("\n============ OPCIONES ===========", False)

                    for idx, youtube_option in enumerate(YOUTUBE_OPTIONS):
                        print(colored(f" {idx + 1}. {youtube_option}", "cyan"))

                    info("=================================\n", False)

                    # Get user input
                    user_input = int(question("Seleccioná una opción: "))
                    tts = TTS()

                    if user_input == 1:
                        youtube.generate_video(tts)
                        upload_to_yt = question("¿Querés subir este video a YouTube? (Sí/No): ")
                        if upload_to_yt.lower() in ("sí", "si", "yes"):
                            youtube.upload_video()
                    elif user_input == 2:
                        videos = youtube.get_videos()

                        if len(videos) > 0:
                            videos_table = PrettyTable()
                            videos_table.field_names = ["ID", "Fecha", "Título"]

                            for video in videos:
                                videos_table.add_row([
                                    videos.index(video) + 1,
                                    colored(video["date"], "blue"),
                                    colored(video["title"][:60] + "...", "green")
                                ])

                            print(videos_table)
                        else:
                            warning(" No se encontraron videos.")
                    elif user_input == 3:
                        info("¿Con qué frecuencia querés subir?")

                        info("\n============ OPCIONES ===========", False)
                        for idx, cron_option in enumerate(YOUTUBE_CRON_OPTIONS):
                            print(colored(f" {idx + 1}. {cron_option}", "cyan"))

                        info("=================================\n", False)

                        user_input = int(question("Seleccioná una opción: "))

                        cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
                        command = ["python", cron_script_path, "youtube", selected_account['id'], get_active_model()]

                        def job():
                            subprocess.run(command)

                        if user_input == 1:
                            # Upload Once
                            schedule.every(1).day.do(job)
                            success("Tarea CRON configurada.")
                        elif user_input == 2:
                            # Upload Twice a day
                            schedule.every().day.at("10:00").do(job)
                            schedule.every().day.at("16:00").do(job)
                            success("Tarea CRON configurada.")
                        else:
                            break
                    elif user_input == 4:
                        if get_verbose():
                            info(" => Volviendo al menú anterior...", False)
                        break
    elif user_input == 2:
        info("Iniciando Bot de Twitter...")

        cached_accounts = get_accounts("twitter")

        if len(cached_accounts) == 0:
            warning("No se encontraron cuentas en caché. ¿Querés crear una ahora?")
            user_input = question("Sí/No: ")

            if user_input.lower() in ("sí", "si", "yes"):
                generated_uuid = str(uuid4())

                success(f" => ID generado: {generated_uuid}")
                nickname = question(" => Ingresá un apodo para esta cuenta: ")
                fp_profile = question(" => Ingresá la ruta al perfil de Firefox: ")
                topic = question(" => Ingresá el tema de la cuenta: ")

                add_account("twitter", {
                    "id": generated_uuid,
                    "nickname": nickname,
                    "firefox_profile": fp_profile,
                    "topic": topic,
                    "posts": []
                })
        else:
            table = PrettyTable()
            table.field_names = ["ID", "UUID", "Apodo", "Tema de la cuenta"]

            for account in cached_accounts:
                table.add_row([cached_accounts.index(account) + 1, colored(account["id"], "cyan"), colored(account["nickname"], "blue"), colored(account["topic"], "green")])

            print(table)
            info("Escribí 'd' para eliminar una cuenta.", False)

            user_input = question("Seleccioná una cuenta para iniciar (o 'd' para eliminar): ").strip()

            if user_input.lower() == "d":
                delete_input = question("Ingresá el número de cuenta a eliminar: ").strip()
                account_to_delete = None

                for account in cached_accounts:
                    if str(cached_accounts.index(account) + 1) == delete_input:
                        account_to_delete = account
                        break

                if account_to_delete is None:
                    error("Cuenta seleccionada inválida. Intentá de nuevo.", "red")
                else:
                    confirm = question(f"¿Estás seguro de que querés eliminar '{account_to_delete['nickname']}'? (Sí/No): ").strip().lower()

                    if confirm in ("sí", "si", "yes"):
                        remove_account("twitter", account_to_delete["id"])
                        success("¡Cuenta eliminada exitosamente!")
                    else:
                        warning("Eliminación de cuenta cancelada.", False)

                return

            selected_account = None

            for account in cached_accounts:
                if str(cached_accounts.index(account) + 1) == user_input:
                    selected_account = account

            if selected_account is None:
                error("Cuenta seleccionada inválida. Intentá de nuevo.", "red")
                main()
            else:
                twitter = Twitter(selected_account["id"], selected_account["nickname"], selected_account["firefox_profile"], selected_account["topic"])

                while True:
                    
                    info("\n============ OPCIONES ===========", False)

                    for idx, twitter_option in enumerate(TWITTER_OPTIONS):
                        print(colored(f" {idx + 1}. {twitter_option}", "cyan"))

                    info("=================================\n", False)

                    # Get user input
                    user_input = int(question("Seleccioná una opción: "))

                    if user_input == 1:
                        twitter.post()
                    elif user_input == 2:
                        posts = twitter.get_posts()

                        posts_table = PrettyTable()

                        posts_table.field_names = ["ID", "Fecha", "Contenido"]

                        for post in posts:
                            posts_table.add_row([
                                posts.index(post) + 1,
                                colored(post["date"], "blue"),
                                colored(post["content"][:60] + "...", "green")
                            ])

                        print(posts_table)
                    elif user_input == 3:
                        info("¿Con qué frecuencia querés publicar?")

                        info("\n============ OPCIONES ===========", False)
                        for idx, cron_option in enumerate(TWITTER_CRON_OPTIONS):
                            print(colored(f" {idx + 1}. {cron_option}", "cyan"))

                        info("=================================\n", False)

                        user_input = int(question("Seleccioná una opción: "))

                        cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
                        command = ["python", cron_script_path, "twitter", selected_account['id'], get_active_model()]

                        def job():
                            subprocess.run(command)

                        if user_input == 1:
                            # Post Once a day
                            schedule.every(1).day.do(job)
                            success("Tarea CRON configurada.")
                        elif user_input == 2:
                            # Post twice a day
                            schedule.every().day.at("10:00").do(job)
                            schedule.every().day.at("16:00").do(job)
                            success("Tarea CRON configurada.")
                        elif user_input == 3:
                            # Post thrice a day
                            schedule.every().day.at("08:00").do(job)
                            schedule.every().day.at("12:00").do(job)
                            schedule.every().day.at("18:00").do(job)
                            success("Tarea CRON configurada.")
                        else:
                            break
                    elif user_input == 4:
                        if get_verbose():
                            info(" => Volviendo al menú anterior...", False)
                        break
    elif user_input == 3:
        info("Iniciando Marketing de Afiliados...")

        cached_products = get_products()

        if len(cached_products) == 0:
            warning("No se encontraron productos en caché. ¿Querés crear uno ahora?")
            user_input = question("Sí/No: ")

            if user_input.lower() in ("sí", "si", "yes"):
                affiliate_link = question(" => Ingresá el enlace de afiliado: ")
                twitter_uuid = question(" => Ingresá el UUID de la cuenta de Twitter: ")

                # Find the account
                account = None
                for acc in get_accounts("twitter"):
                    if acc["id"] == twitter_uuid:
                        account = acc

                add_product({
                    "id": str(uuid4()),
                    "affiliate_link": affiliate_link,
                    "twitter_uuid": twitter_uuid
                })

                afm = AffiliateMarketing(affiliate_link, account["firefox_profile"], account["id"], account["nickname"], account["topic"])

                afm.generate_pitch()
                afm.share_pitch("twitter")
        else:
            table = PrettyTable()
            table.field_names = ["ID", "Enlace de afiliado", "UUID cuenta Twitter"]

            for product in cached_products:
                table.add_row([cached_products.index(product) + 1, colored(product["affiliate_link"], "cyan"), colored(product["twitter_uuid"], "blue")])

            print(table)

            user_input = question("Seleccioná un producto para iniciar: ")

            selected_product = None

            for product in cached_products:
                if str(cached_products.index(product) + 1) == user_input:
                    selected_product = product

            if selected_product is None:
                error("Producto seleccionado inválido. Intentá de nuevo.", "red")
                main()
            else:
                # Find the account
                account = None
                for acc in get_accounts("twitter"):
                    if acc["id"] == selected_product["twitter_uuid"]:
                        account = acc

                afm = AffiliateMarketing(selected_product["affiliate_link"], account["firefox_profile"], account["id"], account["nickname"], account["topic"])

                afm.generate_pitch()
                afm.share_pitch("twitter")

    elif user_input == 4:
        info("Iniciando Outreach...")

        outreach = Outreach()

        outreach.start()
    elif user_input == 5:
        if get_verbose():
            print(colored(" => Saliendo...", "blue"))
        sys.exit(0)
    else:
        error("Opción seleccionada inválida. Intentá de nuevo.", "red")
        main()
    

if __name__ == "__main__":
    # Print ASCII Banner
    print_banner()

    first_time = get_first_time_running()

    if first_time:
        print(colored("¡Hola! Parece que estás ejecutando MoneyPrinter V2 por primera vez. ¡Vamos a configurarlo primero!", "yellow"))

    # Setup file tree
    assert_folder_structure()

    # Remove temporary files
    rem_temp_files()

    # Fetch MP3 Files
    fetch_songs()

    # Select Ollama model — use config value if set, otherwise pick interactively
    configured_model = get_ollama_model()
    if configured_model:
        select_model(configured_model)
        success(f"Usando modelo configurado: {configured_model}")
    else:
        try:
            models = list_models()
        except Exception as e:
            error(f"No se pudo conectar a Ollama: {e}")
            sys.exit(1)

        if not models:
            error("No se encontraron modelos en Ollama. Descargá uno primero (ej: 'ollama pull llama3.2:3b').")
            sys.exit(1)

        info("\n======== MODELOS DE OLLAMA =======", False)
        for idx, model_name in enumerate(models):
            print(colored(f" {idx + 1}. {model_name}", "cyan"))
        info("==================================\n", False)

        model_choice = None
        while model_choice is None:
            raw = input(colored("Seleccioná un modelo: ", "magenta")).strip()
            try:
                choice_idx = int(raw) - 1
                if 0 <= choice_idx < len(models):
                    model_choice = models[choice_idx]
                else:
                    warning("Selección inválida. Intentá de nuevo.")
            except ValueError:
                warning("Por favor ingresá un número.")

        select_model(model_choice)
        success(f"Usando modelo: {model_choice}")

    while True:
        main()
