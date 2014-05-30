# take a backup of Database using pg_dump
# replace the postgres with Database username and the dbname with the Database name
# save it to a tar file
export PGPASSWORD="123456"
pg_dump --username=postgres -h localhost kikar_hamedina > $(date "+%Y%m%d-db-backup")
# upload the DB backup to Dropbox
python upload_backup_to_dropbox.py


#To resotre run this command with <newdbname> and <filename> supplemented.
# <filename> must be accessible
# <newdbname> must be entirely empty
# pg_restore --dbname=<newdbname> --verbose <filename>.tar
