Membre 2 - Filebeat + Logstash Project
=====================================

Contenu du zip:
- filebeat.yml
- logstash/logstash.conf
- logs/auth_app.log

But : this is a small starter project for Member 2 (collect/parse/send logs to Elasticsearch).

How to use (quick):
1) Place this folder in your project workspace and open it in VS Code.
2) Ensure you have Filebeat and Logstash installed (on macOS, using Homebrew is recommended).
   - brew tap elastic/tap
   - brew install elastic/tap/filebeat-full
   - brew install logstash
3) Start Logstash:
   - cd logstash
   - logstash -f logstash.conf
4) Start Filebeat (from the project root where filebeat.yml is):
   - filebeat -e -c filebeat.yml
5) Check Logstash console output; if connected, Filebeat will report successful connection.
6) Open Kibana -> Discover using index pattern: auth-logs-*
   (Make sure Elasticsearch & Kibana are running.)

Notes:
- filebeat.yml uses a relative path ./logs/auth_app.log so run Filebeat from the project root.
- logstash.conf parses the provided log format using GROK; adjust if Member 1 changes the log format.
- auth_app.log contains example lines; Member 1 will generate real logs there in the real project.

Troubleshooting:
- If Filebeat can't connect: check Logstash is listening on port 5044.
- If logs don't appear in Kibana: verify Elasticsearch is reachable at http://localhost:9200 and index auth-logs-* exists.
- If grok parsing fails: test patterns with the Grok Debugger in Kibana or adjust logstash.conf.

Deliverables for Member 2:
- filebeat.yml
- logstash.conf
- Example auth_app.log
- This README

