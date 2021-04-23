from mysite.wsgi import application
import cherrypy

if __name__ == '__main__':
    cherrypy.tree.graft(application, '/crsystem')

    cherrypy.server.unsubscribe()
    
    server = cherrypy._cpserver.Server()
    
    server.socket_host = "0.0.0.0"
    server.socket_port = 8085
    server.thread_pool = 30
    
    server.subscribe()
    
    cherrypy.engine.start()
    cherrypy.engine.block()