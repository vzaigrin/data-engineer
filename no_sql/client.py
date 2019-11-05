import sys
import argparse
import logging
import aerospike
from aerospike import predicates as p


def add_customer(l_client, l_ns, l_st, l_customer_id, l_phone_number, l_lifetime_value):
    key = (l_ns, l_st, l_customer_id)
    try:
        l_client.put(key, {
            'phone': l_phone_number,
            'ltv': l_lifetime_value
        })
    except Exception as e:
        logging.error("error: {0}".format(e))


def get_ltv_by_id(l_client, l_ns, l_st, l_customer_id):
    key = (l_ns, l_st, l_customer_id)
    (key, metadata, record) = l_client.get(key)
    if record == {}:
        logging.error('Requested non-existent customer ' + str(l_customer_id))
    else:
        return record.get('ltv')


def get_ltv_by_phone(l_client, l_ns, l_st, l_phone_number):
    records = l_client.query(l_ns, l_st).select('phone', 'ltv').where(p.equals('phone', l_phone_number)).results()
    if len(records) > 0:
        return records[0][2]['ltv']
    logging.error('Requested phone number is not found ' + str(l_phone_number))


def test(l_client, l_ns, l_st):
    for i in range(0, 1000):
        add_customer(l_client, l_ns, l_st, i, i, i + 1)
    print('test add_customer complete')

    for i in range(0, 1000):
        assert (i + 1 == get_ltv_by_id(l_client, l_ns, l_st, i)), "No LTV by ID " + str(i)
        print('test get_ltv_by_id complete', i)
        assert (i + 1 == get_ltv_by_phone(l_client, l_ns, l_st, i)), "No LTV by phone " + str(i)
        print('test get_ltv_by_phone complete', i)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1', help='Aerospike server address')
    parser.add_argument('--port', type=int, default=3000, help='Aerospike server port')
    parser.add_argument('--namespace', default='test', help='namespace')
    parser.add_argument('--set', default='ltv', help='set')
    parser.add_argument('--add_customer', nargs=3, type=int, help='add customer by customer_id, phone_number, lifetime_value')
    parser.add_argument('--get_ltv_by_id', nargs=1, type=int, help='get lifetime_value by customer_id')
    parser.add_argument('--get_ltv_by_phone', nargs=1, type=int, help='get lifetime_value by phone_number')
    args = vars(parser.parse_args())

    ns = args.get('namespace')
    st = args.get('set')

    # Configure the client
    config = {'hosts': [(args.get('host'), args.get('port'))]}

    # Create a client and connect it to the cluster
    try:
        client = aerospike.client(config).connect()
        # Create index for 'phone' (needs only once)
        # client.index_integer_create(ns, st, 'phone', 'phone_idx')
    except:
        print("failed to connect to the cluster with", config['hosts'])
        sys.exit(1)

    # add_customer
    if args.get('add_customer') is not None:
        customer_id = args.get('add_customer')[0]
        phone_number = args.get('add_customer')[1]
        lifetime_value = args.get('add_customer')[2]
        add_customer(client, ns, st, customer_id, phone_number, lifetime_value)
        print('add_customer: ', customer_id, phone_number, lifetime_value)

    # get_ltv_by_id
    if args.get('get_ltv_by_id') is not None:
        customer_id = args.get('get_ltv_by_id')[0]
        lifetime_value = get_ltv_by_id(client, ns, st, customer_id)
        print('get_ltv_by_id: ', customer_id, lifetime_value)

    # get_ltv_by_phone
    if args.get('get_ltv_by_phone') is not None:
        phone_number = args.get('get_ltv_by_phone')[0]
        lifetime_value = get_ltv_by_phone(client, ns, st, phone_number)
        print('get_ltv_by_phone: ', phone_number, lifetime_value)

    # test if no arguments for functions call
    if args.get('add_customer') is None and args.get('get_ltv_by_id') is None and args.get('get_ltv_by_phone') is None:
        test(client, ns, st)

    # Close the connection to the Aerospike cluster
    client.close()
