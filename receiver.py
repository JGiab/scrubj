import pickle
import zmq
import pprint
import re
from neo4j import GraphDatabase


# Neo4j Functions

def dbhandle(uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver

def dbclose(driver):
    driver.close()

def create_node(driver, loc, fname, ftype, argument_types):
    with driver.session() as session:
        tx = session.begin_transaction()
        create_function_node(tx, loc, fname, ftype, argument_types)
        tx.commit()


def create_function_node(tx, loc, fname, ftype, argument_types):
    tx.run("MERGE (n:function {loc:{loc}, name:{fname}}) \
            ON CREATE SET n.type = {ftype}, \
            n.argument_types = {argument_types} \
            ON MATCH SET n.type = {ftype}, \
            n.argument_types = {argument_types}", loc=loc,
            fname=fname, ftype=ftype, argument_types=argument_types)

            #type:{ftype}, \
            #argument_types:{argument_types}})",
            #{"loc":loc, "fname":fname, "ftype":ftype, \
            #"argument_types":argument_types})


def create_callee_node(driver, loc, fname, parent_name, parent_loc):
    with driver.session() as session:
        tx = session.begin_transaction()
        create_callee_function(tx, loc, fname, parent_name, parent_loc)
        tx.commit()

def create_callee_function(tx, loc, fname, parent_name, parent_loc):
    tx.run("MATCH (f:function) WHERE f.name={parent_name} AND f.loc={parent_loc} \
            MERGE (n:function {loc:{loc}, name:{fname}})<-[:CALLS]-(f)",
            parent_name=parent_name, parent_loc=parent_loc, loc=loc, fname=fname)



def create_caller_edge(driver, loc, fname, callee_name, callee_loc):
    with driver.session() as session:
        tx = session.begin_transaction()
        create_caller_function(tx, loc, fname, callee_name, callee_loc)
        tx.commit()


def create_caller_function(tx, loc, fname, callee_name, callee_loc):
    tx.run("MATCH (f:function) WHERE f.name={callee_name} AND f.loc={callee_loc} \
            MATCH (n:function) WHERE n.name={fname} AND n.loc={loc} \
            CREATE (n)-[:IS_CALLED_BY]->(f)",
            callee_name=callee_name, callee_loc=callee_loc, loc=loc, fname=fname)


# Zeromq PUB-SUB functions
def connect():
    context = zmq.Context()

    # Connect the subscriber socket
    subscriber = context.socket(zmq.SUB)
    subscriber.connect('ipc:///tmp/feeds/0')
    subscriber.setsockopt(zmq.SUBSCRIBE, b'')

    return subscriber

# Where it all goes down
def main():
    subscriber = connect()
    count = 0
    gcc_disconnect = False
    master = {}
    restr = r'(.+)(\@)(.+)'
    rexp = re.compile(restr)


    while True:
        try:
            msg = subscriber.recv()
            if msg == b"GCC_DISCONNECT":
                if gcc_disconnect == False: # When 2000ms pass without receive
                    subscriber.RCVTIMEO = 2000 # the conn will close
                    gcc_disconnect = True # find alternative when possible
                else:
                    continue
            else:
                data = pickle.loads(msg)
                master[count] = data
                pprint.pprint(master[count])
                #data.clear()
                count += 1

        except zmq.error.Again:
            print("gcc disconnected")
            break
        except KeyboardInterrupt:
            print("Interrupt received, stopping...")
            break

    # Add your uri, user and password
    db = dbhandle("uri", "user", "password")

    for key in master:
        temp = master[key]
        m1 = rexp.search(str(temp['parent']))
        #print(str(m.group(3))) this is the loc
        #print(str(m.group(1)))
        #print(str(temp['parent_type']))

        if m1:
            create_node(db, str(m1.group(3)), str(m1.group(1)),
                str(temp['parent_type']), str(temp['parent_argument_types']))

        for callee in temp['callees']:
            m2 = rexp.search(str(callee))

            if m2:
                create_callee_node(db, str(m2.group(3)), str(m2.group(1)),
                        str(m1.group(1)), str(m1.group(3)))

        for caller in temp['callers']:
            m3 = rexp.search(str(callee))

            if m3:
                create_caller_edge(db, str(m3.group(3)), str(m3.group(1)),
                        str(m1.group(1)), str(m1.group(3)))




    dbclose(db)


if __name__ == "__main__":
    main()