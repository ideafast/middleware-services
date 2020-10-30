from fastapi import APIRouter
from dotenv import load_dotenv, find_dotenv
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import os


router = APIRouter()
load_dotenv(find_dotenv('.dtransfer.env'))
base_url = os.getenv("DMP_BASE_URL")
username = os.getenv("DMP_USERNAME")
password = os.getenv("DMP_PASSWORD")
totp = os.getenv("DMP_TOTP")


sample_transport = RequestsHTTPTransport(
    url=f"{base_url}graphql",
    use_json=True,
    headers={
        "Content-type": "application/json",
    }
)
client = Client(
    transport=sample_transport,
    fetch_schema_from_transport=True,
)
login_query = gql('''
        fragment ALL_FOR_USER on User {
            id
            username
            type
            firstname
            lastname
            email
            organisation
            description
            access {
                id
                projects {
                    id
                    name
                    studyId
                }
                studies {
                    id
                    name
                }
            },
            createdAt,
            expiredAt
        }
        
        mutation login($username: String!, $password: String!, $totp: String!) {
          login(username: $username, password: $password, totp: $totp) {
              ...ALL_FOR_USER
          }
        }
    ''')
login_params = {
    "username": username,
    "password": password,
    "totp": totp,
}
client.execute(login_query, login_params)


@router.get('/studies')
async def studies():
    get_studies_query = gql('''
        fragment ALL_FOR_JOB on Job {
            id
            studyId
            projectId
            jobType
            requester
            requestTime
            receivedFiles
            status
            error
            cancelled
            cancelledTime
            data
        }
        
        query getStudy($studyId: String!) {
                getStudy(studyId: $studyId) {
                    id
                    name
                    createdBy
                    jobs {
                        ...ALL_FOR_JOB
                    }
                    projects {
                        id
                        studyId
                        name
                    }
                    roles {
                        id
                        name
                        permissions
                        projectId
                        studyId
                        users {
                            id
                            firstname
                            lastname
                            organisation
                            username
                        }
                    }
                    files {
                        id
                        fileName
                        studyId
                        projectId
                        fileSize
                        description
                        uploadTime
                        uploadedBy
                    }
                    numOfSubjects
                    currentDataVersion
                    dataVersions {
                        id
                        version
                        tag
                        uploadDate
                        jobId
                        extractedFrom
                        fileSize
                        contentId
                        fieldTrees
                    }
                }
            }
    ''')
    get_studies_params = {
        "studyId": "8f223906-809c-41aa-8e58-3d4ee1f694b1",
    }
    get_studies_response = client.execute(get_studies_query, get_studies_query)
    return 'STUDIES'


def run_job():
    print('RUNNING DATA MANAGEMENT PLATFORM JOB')
