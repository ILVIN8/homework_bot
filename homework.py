import logging
import os
import time
import telegram
import requests
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(
    level=logging.DEBUG,
    filename="program.log",
    filemode="w",
    format="%(asctime)s, %(levelname)s, %(message)s",
)


RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def send_message(bot, message):
    """Отправка сообщения пользователю."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Получение списка домашних работ."""
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    request = requests.get(ENDPOINT, headers=HEADERS, params=params)
    response = request.json()
    return response


def check_response(response):
    """Проверка корректности ответа от Практикума."""
    if "homeworks" in response:
        return response["homeworks"]
    else:
        False


def parse_status(homework) -> str:
    """Формирование сообщения о статусе домашней работы."""
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка переменных в локальном хранилище."""
    if (
        os.getenv(
            "PRACTICUM_TOKEN" and "TELEGRAM_TOKEN" and "TELEGRAM_CHAT_ID"
        )
        is not None
    ):
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical(
            "Отсутствуют переменные окружения! Зовите программиста!!!"
        )
        raise NameError("Отсутствуют переменные окружения")

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - 2629743)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) > 0:
                homework = homeworks[0]
                message = parse_status(homework)
                send_message(bot, message)
                logging.info("Сообщение о статусе ДЗ отправлено")

            current_timestamp = response.get("current_date")
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    main()
