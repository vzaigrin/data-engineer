# 1. Разверните и подготовьте окружение

```
******************************************************************
DONE! Connect to Confluent Control Center at http://localhost:9021
******************************************************************
```

# 2. Создайте KSQL Stream WIKILANG

Посмотрите какие топики есть сейчас в системе, и на основе того, в котором вы видите максимальный объем данных создайте stream по имени WIKILANG который фильтрует правки только в разделах национальных языков, кроме английского (поле channel вида #ru.wikipedia), который сделали не боты.

Stream должен содержать следующие поля: createdat, channel, username, wikipage, diffurl

```
CREATE STREAM WIKILANG AS
SELECT createdat, channel, username, wikipage, diffurl
FROM wikipedia
WHERE channel != '#en.wikipedia' AND channel != '#commons.wikimedia' AND NOT username like '%Bot';
```

# 3. Мониторинг WIKILANG

- В KSQL CLI получите текущую статистику вашего стрима: describe extended wikilang;  

Приложите полный ответ на предыдущий запрос к ответу на задание.

```
ksql> describe extended wikilang;

Name                 : WIKILANG
Type                 : STREAM
Key field            : 
Key format           : STRING
Timestamp field      : Not set - using <ROWTIME>
Value format         : AVRO
Kafka topic          : WIKILANG (partitions: 2, replication: 2)

 Field     | Type                      
---------------------------------------
 ROWTIME   | BIGINT           (system) 
 ROWKEY    | VARCHAR(STRING)  (system) 
 CREATEDAT | BIGINT                    
 CHANNEL   | VARCHAR(STRING)           
 USERNAME  | VARCHAR(STRING)           
 WIKIPAGE  | VARCHAR(STRING)           
 DIFFURL   | VARCHAR(STRING)           
---------------------------------------

Queries that write into this STREAM
-----------------------------------
CSAS_WIKILANG_4 : CREATE STREAM WIKILANG WITH (REPLICAS = 2, PARTITIONS = 2, KAFKA_TOPIC = 'WIKILANG') AS SELECT
  WIKIPEDIA.CREATEDAT "CREATEDAT"
, WIKIPEDIA.CHANNEL "CHANNEL"
, WIKIPEDIA.USERNAME "USERNAME"
, WIKIPEDIA.WIKIPAGE "WIKIPAGE"
, WIKIPEDIA.DIFFURL "DIFFURL"
FROM WIKIPEDIA WIKIPEDIA
WHERE (((WIKIPEDIA.CHANNEL <> '#en.wikipedia') AND (WIKIPEDIA.CHANNEL <> '#commons.wikimedia')) AND (NOT (WIKIPEDIA.USERNAME LIKE '%Bot')));

For query topology and execution plan please run: EXPLAIN <QueryId>

Local runtime statistics
------------------------
messages-per-sec:      2.37   total-messages:       358     last-message: 2019-11-06T14:00:30.564Z

(Statistics of the local KSQL server interaction with the Kafka topic WIKILANG)
ksql> 
```

- В KSQL CLI получите текущую статистику WIKIPEDIANOBOT: describe extended wikipedianobot;  

Приложите раздел Local runtime statistics к ответу на задание.  

```
ksql> describe extended wikipedianobot;
...
Local runtime statistics
------------------------
messages-per-sec:      4.80   total-messages:      1455     last-message: 2019-11-06T14:01:10.961Z

(Statistics of the local KSQL server interaction with the Kafka topic WIKIPEDIANOBOT)
ksql> 
```

Почему для wikipedianobot интерфейс показывает также consumer-* метрики?

*Потому что у него есть consumers*

# 4. Добавьте данные из стрима WIKILANG в ElasticSearch
- Добавьте mapping - запустите скрипт set_elasticsearch_mapping_lang.sh
- Добавьте Kafka Connect - запустите submit_elastic_sink_lang_config.sh
- Добавьте index-pattern - Kibana UI -> Management -> Index patterns -> Create Index Pattern -> Index name or pattern: wikilang -> кнопка Create

Используя полученные знания и документацию ответьте на вопросы:  
a) Опишите что делает каждая из этих операций?

- *set_elasticsearch_mapping_lang.sh создаёт mapping для Wikilang в Elasticsearch*
- *submit_elastic_sink_lang_config.sh создаёт Sink Connector к Wikilang для Elasticsearch*
- *index-pattern - создаёт шаблон индекса для подключения к Elasticsearch*

б) Зачем Elasticsearch нужен mapping чтобы принять данные?

*Маппинг (сопоставление) — это процесс определения схемы или структуры документов. Он описывает свойства полей в документе. Свойства поля включают тип данных (например, string, integer и т.д.) и метаданные. Надо рассказать про схему документов, прежде чем индексировать любые данные. *

в) Что дает index-pattern?

*Шаблон индекса содержит набор данных для визуализации.*

# 5. Создайте отчет "Топ10 национальных разделов" на базе индекса wikilang
- Kibana UI -> Visualize -> + -> Data Table -> выберите индекс wikilang
- Select bucket type -> Split Rows, Aggregation -> Terms, Field -> CHANNEL.keyword, Size -> 10, нажмите кнопку Apply changes (выглядит как кнопка Play)
- Сохраните визуализацию под удобным для вас именем

Что вы увидели в отчете?

*Топ 10 национальных разделов Wikipedia по количеству ключевых слов в термах.*

```
CHANNEL.keyword: Descending Count
#fr.wikipedia               302
#de.wikipedia               191
#it.wikipedia               182
#es.wikipedia               167
#ru.wikipedia               134
#zh.wikipedia               114
#en.wiktionary               48
#uk.wikipedia                28
#mediawiki.wikipedia         19
#eo.wikipedia                 4
```

- Нажав маленьку круглую кнопку со стрелкой вверх под отчетом, вы сможете запросить не только таблицу, но и запрос на Query DSL которым он получен.

Приложите тело запроса к заданию.

```
{
  "query": {
    "bool": {
      "must": [
        {
          "match_all": {}
        },
        {
          "range": {
            "CREATEDAT": {
              "gte": 1573048705284,
              "lte": 1573049605284,
              "format": "epoch_millis"
            }
          }
        }
      ],
      "must_not": []
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "aggs": {
    "2": {
      "terms": {
        "field": "CHANNEL.keyword",
        "size": 10,
        "order": {
          "_count": "desc"
        }
      }
    }
  }
}
```