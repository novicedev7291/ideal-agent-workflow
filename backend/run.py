from app.vector_store_test import similarity_check

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print('Usage: python run.py <query>')
        sys.exit(1)

    similarity_check(sys.argv[1])