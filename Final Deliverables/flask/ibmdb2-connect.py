import ibm_db
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=ba99a9e6-d59e-4883-8fc0-d6a8c9f7a08f.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=31321;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA (3).crt;UID=vbz29727;PWD=zgvT4AKDdg9I90uZ",'','')
print(conn)
print("connection successful...")
