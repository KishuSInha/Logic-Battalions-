async function main() {
  const [deployer] = await ethers.getSigners();

  print("Deploying contracts with the account:", deployer.address);

  const HellfireGold = await ethers.getContractFactory("HellfireGold");
  const hellfireGold = await HellfireGold.deploy(1000000);

  console.log("HellfireGold deployed to:", hellfireGold.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
