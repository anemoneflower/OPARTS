import tensorflow as tf

gpus = tf.config.experimental.list_physical_devices('GPU') 
if gpus: 
    try: 
        for gpu in gpus: 
            print("\t\tSET-GPU", gpu)
            tf.config.experimental.set_memory_growth(gpu, True) 

    except:
        print("ERROR")
