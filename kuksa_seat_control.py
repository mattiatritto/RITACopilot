from kuksa_client.grpc import VSSClient, Datapoint
import time

def setup_driver_seat(profile):
    """
    Setup the driver's seat with the given profile settings.

    Parameters:
    - profile: A list containing position, tilt, and height settings.
    """
    seat_settings = [
        ('Vehicle.Cabin.Seat.Row1.DriverSide.Position', 'Position'),
        ('Vehicle.Cabin.Seat.Row1.DriverSide.Tilt', 'Tilt'),
        ('Vehicle.Cabin.Seat.Row1.DriverSide.Height', 'Height')
    ]

    with VSSClient('127.0.0.1', 55556) as client: #'10.51.249.60', 30555
        for setting, name in seat_settings:
            client.set_target_values({setting: Datapoint(profile[seat_settings.index((setting, name))])})
            print(f"Setting {name} to {profile[seat_settings.index((setting, name))]}")
            time.sleep(1)

    print("Finished setting up driver's seat.")

def main():
    # Example profile: position = 50, tilt = 50, height = 50
    profile = [50, 50, 50]
    setup_driver_seat(profile)

if __name__ == "__main__":
    main()
