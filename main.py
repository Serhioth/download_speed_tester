import logging
import time

import httpx


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "download_speed.log",
            encoding="utf-8",
        ),
    ],
)

logger = logging.getLogger(__name__)


class SpeedMeasurementError(Exception):
    """Ошибка измерения скорости скачивания."""


def main(url: str, try_count: int = 10) -> None:
    """Измеряет скорость скачивания файла,
    вычисляет время запросов, количество скачанных данных
    и среднюю скорость скачивания.
    """
    url = url.strip()

    request_times: list[float] = []
    download_times: list[float] = []
    total_downloaded = 0

    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            for try_number in range(1, try_count + 1):
                logger.info(
                    "Выполняю запрос №%d из %d...",
                    try_number,
                    try_count,
                )

                start = time.perf_counter()
                first_byte_time = None
                size = 0

                with client.stream("GET", url) as response:
                    response.raise_for_status()

                    for chunk in response.iter_bytes():
                        if first_byte_time is None:
                            first_byte_time = time.perf_counter()

                        size += len(chunk)

                end = time.perf_counter()

                if first_byte_time is None:
                    first_byte_time = end

                total_time = end - start
                download_time = end - first_byte_time

                request_times.append(total_time)
                download_times.append(download_time)
                total_downloaded += size

                if download_time > 0:
                    speed_mb_s = size / download_time / 1024 / 1024
                else:
                    speed_mb_s = 0

                logger.info("URL: %s", url)
                logger.info("Размер: %.2f MB", size / 1024 / 1024)
                logger.info("Время запроса: %.3f sec", total_time)
                logger.info(
                    "Скорость скачивания: %.2f MB/s",
                    speed_mb_s,
                )

    except httpx.HTTPError as exc:
        raise SpeedMeasurementError(
            f"Ошибка при измерении скорости: {exc}"
        ) from exc

    average_request_time = sum(request_times) / len(request_times)

    # Средняя скорость всей серии измерений.
    total_download_time = sum(download_times)
    average_speed = (
        total_downloaded / total_download_time / 1024 / 1024
        if total_download_time > 0
        else 0
    )

    logger.info("----- Результаты -----")
    logger.info("Количество запросов: %d", try_count)
    logger.info("Среднее время запроса: %.3f sec", average_request_time)
    logger.info(
        "Всего скачано: %.2f MB",
        total_downloaded / 1024 / 1024,
    )
    logger.info(
        "Средняя скорость скачивания: %.2f MB/s",
        average_speed,
    )


if __name__ == "__main__":
    url = input("Ссылка: ")
    main(url)
