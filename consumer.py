import json 
from typing import Optional, Dict, Any
from exceptions.consumer_seek_error import ConsumerSeekError
from confluent_kafka import Consumer, TopicPartition, KafkaError
from config import GENERAL_CONFIG, KAFKA_CONFIG, GIT_CONFIG
from prometheus_manager.prometheus_manager import PrometheusManager
from prometheus_manager.git_prometheus_manager import GitPrometheusManager
from models.job import JobEvent
from formatters.formatter_factory import get_formatter
from enums.event_actions import EventAction
from utils.logger import create_logger

COLLECTORS_NAMESPACE = GENERAL_CONFIG['collectors_namespace']
REPO_URL = GIT_CONFIG['repo_url']
LOCAL_PATH = GIT_CONFIG['local_path']
BRANCH = GIT_CONFIG['branch']

logger = create_logger("consumer")


class ConsumerService:
    def __init__(self):
        self.running = False
        self.consumer: Optional[Consumer] = None
        self.prometheus_manager: Optional[PrometheusManager] = GitPrometheusManager(REPO_URL, LOCAL_PATH, BRANCH)

    @staticmethod
    def _get_filename(maas_pool: str, collector_cluster: str) -> str:
        return f"{collector_cluster}/{maas_pool}/{maas_pool}-collector-values.yaml"

    def start(self):
        self.running = True
        conf = {
            'bootstrap.servers': KAFKA_CONFIG['servers'],
            'group.id': KAFKA_CONFIG['username'],
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
            'security.protocol': KAFKA_CONFIG['security_protocol'],
            'sasl.mechanism': KAFKA_CONFIG['sasl_mechanism'],
            'sasl.username': KAFKA_CONFIG['sasl_username'],
            'sasl.password': KAFKA_CONFIG['sasl_password']
            }

        try:
            self.consumer = Consumer(conf)
            self.consumer.subscribe([KAFKA_CONFIG['topic']])
            logger.info('successfully started consumer')

            while self.running:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"End of partition reached {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                        continue
                    else:
                        continue
                
                try:
                    event_value = json.loads(msg.value().decode('utf-8'))
                    self._process_event(event_value)
                    self.consumer.commit(asynchronous=False)
                except Exception as e:
                    logger.error(f"Failed to process event: {e}")
                    self.prometheus_manager.rollback()
                    self.consumer.seek(tp=TopicPartition(topic=msg.topic(), partition=msg.partition(), offset=msg.offset()))
        except ConsumerSeekError as e:
            logger.critical('seek failed')
            raise e
        except Exception as e:
            logger.error(f'consumer failed: {e}')
        finally:
            if self.consumer:
                self.consumer.close()
                logger.debug('consumer closed')
        
    def _process_event(self, event_value: Dict[str, Any]):
        try:
            event = JobEvent(**event_value)
            
            if event.action in [EventAction.CREATE, EventAction.UPDATE]:
                formatter_cls = get_formatter(job_type=event.job_type)
                event.data = formatter_cls.format_job(data=event.data)
                logger.info(f"formatted job data: {event.data}")
            
            yaml_filename = self._get_filename(event.maas_pool, event.collector_cluster)
            self.prometheus_manager.update_content(action=event.action, job_data=event.job_data, job_name=event.job_name, yaml_filename=yaml_filename)
        except FileExistsError as e:
            logger.error(f"Failed to update content: {e}")
        except Exception as e:
            logger.error(f"Failed to update content: {e}")            
    
    def stop(self):
        self.running = False
    
    def seek(self, tp: TopicPartition):
        try:
            self.consumer.seek(tp)
        except Exception as e:
            logger.error(f"Failed to seek: {e}")
            raise ConsumerSeekError("failed to seek")