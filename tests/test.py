from astrometry_net_client.client import Session


key_location = '/home/sten/Documents/Projects/PracticalAstronomyCrew/key'
filename = 'home/sten/Documents/Projects/PracticalAstronomyCrew/test-data/target.200417.00000088.3x3.FR.fits'

def main():
    s = Session(None, key_location=key_location)

    print('Loggin in')
    s.login()

    print(s)
    print(s.id)
    print(s.username)


if __name__ == '__main__':
    main()



