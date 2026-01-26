import datetime
import os.path
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

'''
credentials.json = arquivo de configuração e credenciais do projeto GCP.
token.json = arquivo que armazena o token de acesso do usuário.
'''

def create_event(ano: int, mes: int, dia: int, hora_inicio: int, minuto_inicio: int, hora_fim: int, minuto_fim: int, resumo: str, descricao: str) -> dict:
  '''
  Cria um evento no Google Calendar do usuário autenticado.
  
  A função conecta-se à API do Google Calendar usando credenciais armazenadas em 'token.json'
  e cria um novo evento no calendário primário do usuário com os parâmetros fornecidos.
  
  Parâmetros:
  -----------
  ano : int
      Ano do evento (ex: 2026)
  mes : int
      Mês do evento (1-12)
  dia : int
      Dia do evento (1-31)
  hora_inicio : int
      Hora de início do evento no formato 24h (0-23)
  minuto_inicio : int
      Minuto de início do evento (0-59)
  hora_fim : int
      Hora de término do evento no formato 24h (0-23)
  minuto_fim : int
      Minuto de término do evento (0-59)
  resumo : str
      Título/nome do evento que aparecerá no calendário
  descricao : str
      Descrição detalhada do evento (pode ser vazia)
  
  Retorna:
  --------
  dict ou str
      Se sucesso: dicionário com dados do evento criado, incluindo 'htmlLink' para acessá-lo
      Se falha: string 'Event not created'
  
  Exemplo:
  --------
  >>> event = create_event(2026, 1, 26, 14, 30, 15, 30, "Reunião", "Reunião com equipe")
  >>> print(f"Evento criado: {event.get('htmlLink')}")
  '''
  creds = ...
  SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.readonly"]

  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  service = build("calendar", "v3", credentials=creds)
  start_event = datetime.datetime(ano, mes, dia, hora_inicio, minuto_inicio, 00, tzinfo=ZoneInfo('America/Sao_Paulo')).isoformat()
  end_event = datetime.datetime(ano, mes, dia, hora_fim, minuto_fim, 00, tzinfo=ZoneInfo('America/Sao_Paulo')).isoformat()
  event = service.events().insert(
      calendarId="primary",
      body={
        "summary": resumo,
        "description": descricao,
        "start": {
          "dateTime": start_event,
          "timeZone": "America/Sao_Paulo"
        },
        "end": {
          "dateTime": end_event,
          "timeZone": "America/Sao_Paulo"
        }
      }
    ).execute()

  if event.get('status') == 'confirmed':
    return event
  else: 
    return ('Event not created')
  
if __name__ == "__main__":
  x = create_event(2026, 1, 26, 14, 0, 15, 0, "Reunião de Teste", "Descrição da reunião de teste")
  print(x)